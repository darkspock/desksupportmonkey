# Slicing: E4 - Real-time & Notifications

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-15

---

## Feature Breakdown

| Feature | Description | User Stories | Complexity | Status |
|---|---|---|---|---|
| **F0** | Notification Entity + Storage + Endpoints | US-003, US-004 | Medium | Done |
| **F1** | Event Bus + Target Resolver | US-002, US-006 | High | Done |
| **F2** | Event Emission from Request Commands | US-002 (integration) | Medium | Done |
| **F3** | WebSocket + Real-Time Push | US-001, US-005 | High | Done |

---

## F0: Notification Entity + Storage + Endpoints

**Scope:** Notification entity, repository, CRUD endpoints (list, mark read, mark all read), migration.

**Why F0:** The notification entity and persistence must exist before events can create notifications. The REST endpoints are also independent of WebSocket and event bus — they just read/write notification records.

**Includes:**
- Notification entity (dataclass) + EventType enum
- NotificationRepositoryInterface + NotificationRepository
- NotificationModel (SQLAlchemy, ULIDMixin)
- CreateNotification command (internal — used by subscriber, not exposed via HTTP)
- MarkRead command + MarkAllRead command
- ListNotifications query (paginated, filter by is_read, unread_count in meta)
- Extend my/routers.py with 3 notification endpoints
- Extend my/schemas.py with notification response schemas
- Alembic migration for notifications table
- models_registry.py update

**Endpoints:**
- `GET /api/v1/my/notifications` — list notifications (any authenticated user)
- `PATCH /api/v1/my/notifications/{id}/read` — mark single as read
- `PATCH /api/v1/my/notifications/read-all` — mark all as read

---

## F1: Event Bus + Target Resolver

**Scope:** DomainEvent value object, event bus (pub/sub), target resolver (who gets notified), notification subscriber (creates records).

**Why F1:** The event bus is the core routing mechanism. The target resolver encapsulates all notification targeting rules. The notification subscriber connects events to persistent notification creation. Must exist before events can be emitted (F2) or pushed via WebSocket (F3).

**Depends on:** F0 (Notification entity and repository must exist for subscriber to create records)

**Includes:**
- DomainEvent dataclass (value object — event_type, company_id, actor_id, target_user_ids, payload, title, body, timestamp)
- EventBus service (publish, subscribe, dispatch to subscribers)
- TargetResolver service (resolves event_type + context → list of target user_ids)
- NotificationSubscriber (receives events, creates Notification records via repository)
- Targeting rules implementation for all 6 event types
- Unit tests for event bus, target resolver, notification subscriber

---

## F2: Event Emission from Request Commands

**Scope:** Modify existing request routers to emit domain events after successful command execution.

**Why F2:** This connects the event producers (request commands) to the event bus. Must come after F1 (event bus exists) and before F3 (WebSocket needs events to push).

**Depends on:** F1 (event bus and subscribers must exist)

**Includes:**
- Inject EventBus into request routers
- Emit events after each command: create_request, change_status, change_priority, assign_request, add_comment, add_note
- Event enrichment: build DomainEvent with proper title/body/payload for each event type
- Integration tests: verify that command execution → notification creation

**Modified files:**
- `adapters/http/api/requests/routers.py` — emit events after commands
- Possibly extract event building into a helper/factory

---

## F3: WebSocket + Real-Time Push

**Scope:** WebSocket endpoint with JWT auth, connection manager, WebSocket subscriber, real-time push.

**Why F3:** Last because it depends on the full event pipeline being in place (F0 storage, F1 routing, F2 emission). The WebSocket layer is additive — everything works without it (notifications still stored and queryable via REST).

**Depends on:** F1 (event bus to subscribe to), F2 (events being emitted)

**Includes:**
- ConnectionManager (in-memory registry: user_id → list of WebSocket connections)
- WebSocket endpoint (`/ws?token=<jwt>`) with JWT validation
- WebSocketSubscriber (receives events from event bus, pushes to connected users)
- Graceful connection/disconnection handling
- Push message format (JSON with type + data)
- Unread count push alongside notifications
- Mount WebSocket route in app.py
- Integration tests: connect, receive notification, disconnect

**Endpoints:**
- `ws://host/ws?token=<jwt>` — WebSocket connection

---

## Dependency Graph

```
F0: Notification Entity + Storage + Endpoints
 │
 └── F1: Event Bus + Target Resolver
      │
      └── F2: Event Emission from Request Commands
           │
           └── F3: WebSocket + Real-Time Push
```

E4 is strictly sequential: each feature builds on the previous one. F0 creates the storage layer, F1 creates the routing layer, F2 connects producers, F3 adds real-time delivery.

---

## Implementation Order

1. **F0** — Notification entity, repository, REST endpoints, migration
2. **F1** — Event bus, target resolver, notification subscriber
3. **F2** — Emit domain events from request command routers
4. **F3** — WebSocket endpoint, connection manager, real-time push

---

## Migration Strategy

**Single migration in F0:** Create the `notifications` table with all columns and indexes upfront. No additional migrations needed for F1-F3 (they add application logic, not schema changes).
