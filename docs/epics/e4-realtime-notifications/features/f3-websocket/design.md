# Design: F3 - WebSocket + Real-Time Push

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F3 adds WebSocket infrastructure and connects it to the event bus.

```
NEW FILES:
src/notification_bc/notification/infrastructure/connection_manager.py  # WebSocket registry
src/notification_bc/notification/application/services/websocket_subscriber.py  # Push to WS
adapters/http/ws/
├── __init__.py
└── websocket.py              # WebSocket endpoint

MODIFIED FILES:
app.py                         # Mount WebSocket route
adapters/http/api/dependencies.py  # Register WebSocketSubscriber on EventBus
```

---

## ConnectionManager

```python
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws != websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id not in self._connections:
            return
        broken = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                broken.append(ws)
        for ws in broken:
            self.disconnect(user_id, ws)

    async def send_to_users(self, user_ids: list[str], message: dict):
        for uid in user_ids:
            await self.send_to_user(uid, message)
```

Singleton instance, shared across the app.

---

## WebSocket Endpoint

```python
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        payload = decode_jwt(token)
        user_id = payload["sub"]
        company_id = payload["company_id"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive, receive client messages (for future use)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

---

## WebSocketSubscriber

```python
class WebSocketSubscriber:
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager

    def __call__(self, event: DomainEvent, db: Session):
        # Resolve targets (same as notification subscriber)
        # For each target, push notification via WebSocket
        # Also push unread_count update
        import asyncio
        loop = asyncio.get_event_loop()
        # Run async send in sync context
        ...
```

**Challenge:** The event bus is synchronous (called from sync FastAPI endpoints), but WebSocket send is async. Solutions:
1. Use `asyncio.create_task()` if running in async context
2. Use `asyncio.run_coroutine_threadsafe()` if sync
3. **Recommended:** Make the request endpoints async, or queue the push and process in background

For v1, simplest approach: store pending pushes and process them via a FastAPI middleware/dependency that runs after response, or use `asyncio.get_event_loop().create_task()`.

**Alternative (simpler):** Make the WebSocketSubscriber accumulate messages, then have the router flush them after the response. This avoids async/sync mixing.

**Final approach:** Use `anyio.from_thread.run` or simply make the relevant endpoints `async def` and use `await` for the event bus publish. Since FastAPI supports both sync and async, this is feasible.

---

## App Integration

In `app.py`:
```python
from adapters.http.ws.websocket import router as ws_router
app.include_router(ws_router)
```

The ConnectionManager singleton is created in the ws module and imported by the WebSocketSubscriber.
