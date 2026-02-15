import logging
from typing import Any

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws is not websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        if user_id not in self._connections:
            return
        broken: list[WebSocket] = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                broken.append(ws)
        for ws in broken:
            self.disconnect(user_id, ws)

    async def send_to_users(self, user_ids: list[str], message: dict[str, Any]) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, message)

    def is_connected(self, user_id: str) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0

    @property
    def active_connections_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


connection_manager = ConnectionManager()
