# Requirements: F3 - WebSocket + Real-Time Push

**Epic:** [E4 - Real-time & Notifications](../../requirements.md)
**Date:** 2026-02-15

---

## Overview

Deliver the WebSocket endpoint with JWT authentication, an in-memory connection manager, and a WebSocket subscriber that pushes notifications to connected users in real-time.

---

## Requirements

### R1: WebSocket Endpoint
- `ws://host/ws?token=<jwt>` establishes a WebSocket connection
- JWT is validated on connect (decode, verify expiry, extract user_id and company_id)
- Invalid/expired JWT → close with code 4001 and reason "Invalid token"
- On successful connect, user is registered in ConnectionManager
- On disconnect, user is removed from ConnectionManager

### R2: ConnectionManager
- In-memory registry: maps user_id → list of WebSocket connections
- Supports multiple connections per user (multiple tabs/devices)
- `connect(user_id, websocket)` — add connection
- `disconnect(user_id, websocket)` — remove connection
- `send_to_user(user_id, message)` — send JSON to all connections for a user
- `send_to_users(user_ids, message)` — send to multiple users
- Graceful handling of broken connections (remove silently on send failure)

### R3: WebSocketSubscriber
- Registered on the EventBus alongside NotificationSubscriber
- When an event is published, pushes to all target users' active WebSocket connections
- Message format:
  ```json
  {"type": "notification", "data": {"id": "...", "event_type": "...", "title": "...", "body": "...", "data": {...}, "created_at": "..."}}
  ```
- Also sends unread count update:
  ```json
  {"type": "unread_count", "data": {"count": N}}
  ```
- If user is not connected, no-op (notification is still stored via NotificationSubscriber)

### R4: Keep-Alive
- Server sends ping every 30 seconds to detect stale connections
- Stale connections (no pong response) are removed from ConnectionManager

---

## Acceptance Criteria

- [ ] WebSocket connection with valid JWT succeeds
- [ ] WebSocket connection with invalid JWT rejected (4001)
- [ ] Multiple connections per user supported
- [ ] Real-time push when domain event targets the user
- [ ] Push message format includes notification data
- [ ] Unread count pushed alongside notification
- [ ] Disconnected users cleaned up
- [ ] Keep-alive ping/pong works
- [ ] Integration test: connect → trigger event → receive push → disconnect
