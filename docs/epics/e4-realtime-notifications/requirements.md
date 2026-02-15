# Epic E4: Real-time & Notifications

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-15
**Priority:** Medium
**Depends on:** E3 (Service Requests)

---

## Business Alignment

**Objective:** Deliver real-time push notifications and an in-app notification system so users are immediately aware of relevant changes to service requests and assets — without polling or manual refresh.

E0-E3 built authentication, company management, asset inventory, and the full service request lifecycle. But currently, users must manually refresh to discover status changes, new comments, or assignment updates. E4 bridges this gap by introducing WebSocket-based real-time delivery, a pub/sub event bus for decoupled event routing, and persistent in-app notifications with read/unread tracking. This is a prerequisite for the frontend (E7) to deliver a responsive, modern user experience.

---

## Problem Statement

### Current Situation
E0-E3 delivered a fully functional API. But:
- No way to notify users when a request changes status
- No way to alert technicians when new requests arrive or are assigned to them
- No push mechanism for comments or notes added to requests
- No in-app notification inbox for users to review missed events
- No event bus to decouple producers (commands) from consumers (notifications, audit)
- Users must poll or manually refresh to discover changes

### What E4 Delivers
A real-time notification system where:
- WebSocket connections are established per-user with JWT authentication
- Domain events are emitted when significant state changes occur (request created, status changed, assigned, comment added, etc.)
- An event bus routes events to subscribers (notification creator, WebSocket broadcaster, future audit logger)
- In-app notifications are stored persistently with read/unread state
- Real-time push delivers events to connected users instantly via WebSocket
- Users can view, mark as read, and manage their notification inbox

---

## Proposed Solution

### US-E4-001: WebSocket Connection (Per User)
**As a** logged-in user
**I want** to establish a persistent WebSocket connection
**So that** I receive real-time updates without refreshing the page

**Acceptance Criteria:**
- [ ] `ws://host/ws` establishes a WebSocket connection
- [ ] Connection requires a valid JWT token (passed as query parameter `?token=`)
- [ ] Each user has their own connection (1:1 user-to-connection)
- [ ] Multiple connections per user are supported (e.g., multiple tabs)
- [ ] Server sends JSON messages with event type and payload
- [ ] Connection is scoped by company_id (users only receive events for their company)
- [ ] Invalid or expired JWT rejects the connection with 4001 close code
- [ ] Graceful handling of disconnects and reconnects (client-side concern, server cleans up)

### US-E4-002: Domain Event Bus
**As a** developer
**I want** a pub/sub event bus for domain events
**So that** I can decouple event producers from consumers

**Acceptance Criteria:**
- [ ] Event bus supports publishing domain events
- [ ] Multiple subscribers can register for specific event types
- [ ] Built-in subscribers: notification creator, WebSocket broadcaster
- [ ] Events are processed synchronously within the same request (no Celery for v1)
- [ ] Event bus is injectable as a dependency
- [ ] Events carry: event_type, payload, company_id, actor_id, target_user_ids, timestamp
- [ ] Event types: `request.created`, `request.status_changed`, `request.assigned`, `request.priority_changed`, `request.comment_added`, `request.note_added`

### US-E4-003: In-App Notification Storage
**As a** user
**I want** notifications stored so I can review them later
**So that** I don't miss updates when I'm offline or away

**Acceptance Criteria:**
- [ ] Notifications are stored in a `notifications` table
- [ ] Each notification has: id, user_id, company_id, event_type, title, body, data (JSON), is_read, created_at
- [ ] Notifications are created for target users when domain events are emitted
- [ ] Target user resolution: request creator gets notified of status changes, assigned technician gets notified of comments, all company technicians get notified of new requests
- [ ] `GET /api/v1/my/notifications` lists notifications for the current user
- [ ] Pagination with page and page_size
- [ ] Filter by is_read (true/false/all)
- [ ] Default sort: created_at desc (newest first)
- [ ] Response includes unread_count in meta

### US-E4-004: Mark Notifications as Read
**As a** user
**I want** to mark notifications as read
**So that** I can track which updates I've already seen

**Acceptance Criteria:**
- [ ] `PATCH /api/v1/my/notifications/{id}/read` marks a single notification as read
- [ ] `PATCH /api/v1/my/notifications/read-all` marks all unread notifications as read
- [ ] Only the notification owner can mark their notifications
- [ ] Returns updated notification or success confirmation
- [ ] Unread count is updated accordingly

### US-E4-005: Real-Time Push via WebSocket
**As a** connected user
**I want** to receive push notifications in real-time
**So that** I see updates immediately without refreshing

**Acceptance Criteria:**
- [ ] When a domain event targets a user, the event is pushed to all their active WebSocket connections
- [ ] Push message format: `{"type": "notification", "data": {"id": "...", "event_type": "...", "title": "...", "body": "...", "created_at": "..."}}`
- [ ] Events pushed: request status changed, request assigned, comment added (to request creator), new request (to all technicians in company)
- [ ] Notes are NOT pushed to employees (technician-only visibility preserved)
- [ ] If user is not connected, notification is still stored (fetched on next login)
- [ ] Unread count update is pushed alongside each notification: `{"type": "unread_count", "data": {"count": N}}`

### US-E4-006: Notification Targeting Rules
**As a** system
**I want** clear rules for who receives each notification
**So that** users only get relevant notifications

**Acceptance Criteria:**
- [ ] `request.created` → all technicians in the company
- [ ] `request.status_changed` → request creator + assigned technician (if different from actor)
- [ ] `request.assigned` → the assigned technician (if different from actor)
- [ ] `request.priority_changed` → assigned technician (if any, and different from actor)
- [ ] `request.comment_added` → request creator + assigned technician (excluding the comment author)
- [ ] `request.note_added` → assigned technician (excluding the note author, technician-only)
- [ ] Actor (the user who triggered the event) is NEVER notified of their own action

---

## Entities

| Entity | Description | New in E4? |
|---|---|---|
| `Notification` | Persistent in-app notification | New |
| `DomainEvent` | Transient event object for pub/sub routing | New (value object, not persisted) |

### Notification Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `user_id` | ULID | FK to User, NOT NULL, indexed |
| `company_id` | ULID | FK to Company, NOT NULL |
| `event_type` | string(50) | request.created, request.status_changed, etc. |
| `title` | string(255) | Human-readable title |
| `body` | text | Human-readable description |
| `data` | JSON | Event-specific payload (request_id, old_status, new_status, etc.) |
| `is_read` | boolean | Default false |
| `created_at` | datetime | Auto |

**Indexes:** `(user_id, is_read, created_at)`, `(user_id, created_at)`

### DomainEvent (Value Object — not persisted)

| Field | Type | Notes |
|---|---|---|
| `event_type` | string | e.g., `request.status_changed` |
| `company_id` | ULID | Scoping |
| `actor_id` | ULID | Who triggered the event |
| `target_user_ids` | list[str] | Who should receive the notification |
| `payload` | dict | Event-specific data |
| `title` | string | Human-readable notification title |
| `body` | string | Human-readable notification body |
| `timestamp` | datetime | When the event occurred |

---

## Use Cases

### UC-E4-001: Receive Real-Time Status Update
**Actor:** Employee
**Preconditions:** Employee submitted a request, has active WebSocket connection

**Main Flow:**
1. Technician changes request status from `in_review` to `in_progress`
2. Change status command handler emits `request.status_changed` domain event
3. Event bus routes event to notification subscriber and WebSocket subscriber
4. Notification subscriber creates Notification record for the request creator
5. WebSocket subscriber pushes event to employee's active connections
6. Employee sees status update in real-time

**Alternative Flows:**
- A1: Employee not connected → notification stored, delivered on next page load
- A2: Technician is also the request creator → technician does NOT receive notification for own action

### UC-E4-002: Technician Notified of New Request
**Actor:** System (automatic)
**Preconditions:** Employee creates a new request

**Main Flow:**
1. Employee submits a new service request
2. Create request command emits `request.created` domain event
3. Event bus resolves targets: all active technicians in the company
4. Notification records created for each technician
5. WebSocket push sent to all connected technicians
6. Technicians see new request alert in real-time

### UC-E4-003: Review Notification Inbox
**Actor:** User
**Preconditions:** User has received notifications

**Main Flow:**
1. User opens notification inbox (`GET /api/v1/my/notifications`)
2. System returns paginated notifications sorted by newest first
3. User sees unread count in response meta
4. User clicks on a notification, marking it as read
5. System updates is_read flag and decrements unread count

**Alternative Flows:**
- A1: User marks all as read → bulk update, unread count goes to 0
- A2: No unread notifications → unread_count = 0, empty or all-read list

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `core/models_registry.py` | Add NotificationModel | Update imports |
| `app.py` | Mount WebSocket route, register notification endpoints | Update app setup |
| `adapters/http/api/my/routers.py` | Add notification list + mark-read endpoints | Modify existing file |
| `adapters/http/api/my/schemas.py` | Add notification schemas | Modify existing file |
| Request command handlers | Emit domain events after mutations | Modify 6 existing command files |
| Alembic | New migration for notifications table | Generate migration |

---

## Bounded Context

```
src/notification_bc/
├── notification/
│   ├── domain/
│   │   ├── entities.py          # Notification, DomainEvent
│   │   ├── enums.py             # EventType enum
│   │   └── repository.py        # NotificationRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_notification.py
│   │   │   ├── mark_read.py
│   │   │   └── mark_all_read.py
│   │   ├── queries/
│   │   │   └── list_notifications.py
│   │   └── services/
│   │       ├── event_bus.py          # EventBus: publish + subscribe
│   │       ├── notification_subscriber.py  # Creates Notification records
│   │       ├── websocket_subscriber.py     # Pushes to WebSocket connections
│   │       └── target_resolver.py    # Resolves event → target user_ids
│   └── infrastructure/
│       ├── models.py            # NotificationModel
│       ├── repository.py        # NotificationRepository
│       └── connection_manager.py # WebSocket connection registry

adapters/http/
├── ws/
│   └── websocket.py             # WebSocket endpoint with JWT auth
├── api/my/
│   ├── routers.py               # Extend with notification endpoints
│   └── schemas.py               # Extend with notification schemas
```

---

## Technical Decisions

### 1. In-Process Event Bus (No Celery for v1)
Domain events are dispatched synchronously within the same HTTP request. This keeps the architecture simple:
- Command handler emits events → event bus dispatches to subscribers → subscribers create notifications + push WebSocket
- No async task queue needed for notifications in v1
- If performance becomes an issue later, subscribers can be moved to Celery tasks

### 2. WebSocket via FastAPI Native Support
FastAPI has built-in WebSocket support. No need for Socket.IO or external libraries:
- Use `@app.websocket("/ws")` endpoint
- JWT validation from query parameter (`?token=`)
- In-memory connection registry (ConnectionManager) keyed by user_id
- Multiple connections per user (list of WebSocket objects per user_id)

### 3. Redis Pub/Sub for Multi-Worker (Future-Ready)
For v1, the ConnectionManager is in-memory (single-worker). If deployed with multiple uvicorn workers later, Redis pub/sub can be added to broadcast across workers. The architecture supports this by keeping the WebSocket subscriber abstracted.

### 4. Target Resolution as Separate Service
A TargetResolver service encapsulates the rules for "who gets notified" per event type. This keeps notification logic out of command handlers and makes rules easy to modify.

### 5. Notification Creator vs WebSocket Broadcaster
Two separate subscribers:
- **NotificationSubscriber:** Creates persistent Notification records (for inbox)
- **WebSocketSubscriber:** Pushes to active connections (for real-time)

Both run on every event, ensuring notifications are both stored AND pushed.

---

## Definition of Done

- [ ] WebSocket endpoint with JWT authentication works
- [ ] Multiple connections per user supported
- [ ] Event bus publishes and routes domain events
- [ ] Notification records created for target users on each event
- [ ] Target resolution follows defined rules (US-E4-006)
- [ ] Actor never receives notification for own action
- [ ] Notifications list endpoint with pagination and is_read filter
- [ ] Mark single notification as read
- [ ] Mark all notifications as read
- [ ] Unread count included in response meta
- [ ] Real-time push via WebSocket to connected users
- [ ] Notes visibility preserved (no note notifications to employees)
- [ ] Request command handlers emit domain events
- [ ] Alembic migration creates notifications table
- [ ] Unit tests for event bus, target resolver, notification commands/queries
- [ ] WebSocket integration test (connect, receive push, disconnect)

---

## Open Questions

1. **Event persistence:** Should domain events be stored in a dedicated table for replay/audit? **Recommend:** No for v1. RequestEvent already records mutations in E3. DomainEvent is transient — used only for routing to subscribers. If an audit log is needed later, add a third subscriber.
2. **Notification expiry:** Should old notifications be auto-deleted? **Recommend:** Not in v1. Add a Celery beat task later if needed (e.g., delete read notifications older than 90 days).
3. **Email notifications:** Should status changes trigger email in addition to in-app? **Recommend:** Defer to a future enhancement. The event bus architecture makes it trivial to add an EmailSubscriber later.
4. **WebSocket heartbeat:** Should the server send periodic pings? **Recommend:** Yes — FastAPI/Starlette handles WebSocket ping/pong by default. Add a 30-second keep-alive ping to detect stale connections.
5. **Batch notification creation:** When a new request is created and 10 technicians need to be notified, should we batch-insert? **Recommend:** Yes — use `session.add_all()` for bulk insert. Acceptable for v1 since technician counts per company are typically small (<50).
