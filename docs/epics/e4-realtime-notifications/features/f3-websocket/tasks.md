# Tasks: F3 - WebSocket + Real-Time Push

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Infrastructure

### T1.1: Create ConnectionManager
- **File:** `src/notification_bc/notification/infrastructure/connection_manager.py` (NEW)
- In-memory dict: user_id → list[WebSocket]
- Methods: connect, disconnect, send_to_user, send_to_users
- Graceful handling of broken connections
- Singleton instance

---

## Phase 2: WebSocket Endpoint

### T2.1: Create WebSocket route
- **File:** `adapters/http/ws/websocket.py` (NEW)
- `@router.websocket("/ws")` endpoint
- Extract JWT from query param `?token=`
- Validate token using core/jwt.py decode
- On success: register in ConnectionManager, listen loop
- On failure: close with code 4001
- On disconnect: remove from ConnectionManager

### T2.2: Create __init__.py
- `adapters/http/ws/__init__.py`

### T2.3: Mount WebSocket router in app.py
- **File:** `app.py` (MODIFY)
- Import and include ws router

---

## Phase 3: WebSocket Subscriber

### T3.1: Create WebSocketSubscriber
- **File:** `src/notification_bc/notification/application/services/websocket_subscriber.py` (NEW)
- Callable receiving (event, db)
- Uses TargetResolver to get target user_ids
- Uses ConnectionManager to push notification message to connected users
- Also pushes unread_count (queries NotificationRepository.count_unread)
- Handles async/sync bridge (use asyncio to run coroutines from sync context)

### T3.2: Register WebSocketSubscriber on EventBus
- **File:** `adapters/http/api/dependencies.py` (MODIFY)
- Add WebSocketSubscriber alongside NotificationSubscriber

---

## Phase 4: Tests

### T4.1: Unit tests - ConnectionManager
- **File:** `tests/unit/notification_bc/notification/infrastructure/test_connection_manager.py` (NEW)
- Connect adds user
- Disconnect removes user
- Multiple connections per user
- send_to_user delivers to all connections
- Broken connection removed silently

### T4.2: Unit tests - WebSocketSubscriber
- **File:** `tests/unit/notification_bc/notification/application/services/test_websocket_subscriber.py` (NEW)
- Pushes to connected targets
- No-op for disconnected targets
- Correct message format

### T4.3: Integration test - WebSocket endpoint
- **File:** `tests/integration/test_websocket.py` (NEW)
- Connect with valid JWT → accepted
- Connect with invalid JWT → rejected with 4001
- Connect with no token → rejected
- Receive push after event publication

---

## Phase 5: Verification

### T5.1: Run all tests
### T5.2: Manual verification
1. Start server
2. Connect via WebSocket client (wscat or similar) with valid JWT
3. Create a request via API
4. Verify technician WebSocket receives notification push
5. Change status → verify request creator receives push
6. Disconnect → verify ConnectionManager cleanup

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Infrastructure | T1.1 | 1 | -- |
| 2. WebSocket | T2.1-T2.3 | 2 + init | 1 (app.py) |
| 3. Subscriber | T3.1-T3.2 | 1 | 1 (dependencies.py) |
| 4. Tests | T4.1-T4.3 | 3 | -- |
| 5. Verification | T5.1-T5.2 | -- | -- |
