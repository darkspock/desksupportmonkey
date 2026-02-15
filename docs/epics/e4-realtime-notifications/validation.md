# Validation: E4 - Real-time & Notifications

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Codebase Alignment Check

### Existing Patterns to Follow

| Pattern | Source | Apply to E4 |
|---|---|---|
| Entity as dataclass | `src/request_bc/request/domain/entities.py` | Notification entity |
| Repository interface (ABC) | `src/request_bc/request/domain/repository.py` | NotificationRepositoryInterface |
| ULIDMixin + TimestampMixin | `core/mixins.py` | NotificationModel (needs updated_at for is_read changes) |
| Command + Handler pattern | `src/request_bc/request/application/commands/` | Mark read, mark all read |
| Query + Handler pattern | `src/request_bc/request/application/queries/` | List notifications |
| Router with DI | `adapters/http/api/my/routers.py` | Notification endpoints in my router |
| Pydantic schemas | `adapters/http/api/my/schemas.py` | Notification schemas |
| Pagination with PaginationMeta | `adapters/http/schemas/responses.py` | List notifications |
| CommandBus with events | `src/framework/application/command_bus.py` | dispatch_with_events() already supports event collection |

### Existing Infrastructure to Reuse

| Component | Location | Usage in E4 |
|---|---|---|
| `get_db` | `core/database.py` | DB session dependency |
| `get_current_user` | `adapters/http/api/auth/dependencies.py` | WebSocket JWT validation, notification ownership |
| `require_role()` | `adapters/http/api/auth/dependencies.py` | Not needed — all authenticated users get notifications |
| `PaginationMeta` | `adapters/http/schemas/responses.py` | List notifications response |
| `UserRepository` | `src/auth_bc/user/infrastructure/repository.py` | Resolve target technicians by company |
| `core/jwt.py` | JWT decode/verify | WebSocket token validation |
| `core/config.py` | Redis URL available | Future: Redis pub/sub for multi-worker |
| `websockets>=15.0.1` | `pyproject.toml` | WebSocket support already installed |
| `CommandBus.dispatch_with_events()` | `src/framework/application/command_bus.py` | Collect domain events from handlers |
| SQLAlchemy v2 notation | All models | `mapped_column()`, `Mapped[]`, `select()` |

### Key Decision: In-Process Event Bus (No Celery)

For v1, domain events are processed synchronously within the HTTP request lifecycle. The event bus dispatches to subscribers in-process. This avoids the complexity of async task coordination while keeping the architecture extensible — subscribers can be moved to Celery tasks later if latency becomes an issue.

### Key Decision: ULIDMixin Only for Notification (No TimestampMixin)

Notifications use `ULIDMixin` only. The `created_at` comes from `ULIDMixin` or a simple column. There is no `updated_at` — `is_read` is toggled via a direct UPDATE statement, not through entity-level modification. This keeps notifications lightweight and append-mostly.

**Update:** Actually, `ULIDMixin` only provides `id`. We need `created_at` as a `mapped_column`. No `updated_at` needed since marking as read is a simple boolean flip.

### Key Decision: WebSocket Auth via Query Parameter

Since WebSocket upgrade requests cannot carry custom HTTP headers from browser clients, JWT is passed as a query parameter: `ws://host/ws?token=<jwt>`. The server validates the token on connection and rejects with close code 4001 if invalid.

---

## Dependency Check

### Required from E0 (All Exist)

- [x] FastAPI app with router registration — `app.py`
- [x] Base model classes (ULIDMixin) — `core/mixins.py`
- [x] Database session dependency (get_db) — `core/database.py`
- [x] JWT authentication + decode — `core/jwt.py`
- [x] RBAC with role hierarchy — `adapters/http/api/auth/dependencies.py`
- [x] Redis configuration — `core/config.py` (CelerySettings with Redis URL)

### Required from E1 (All Exist)

- [x] User model with company_id — `src/auth_bc/user/infrastructure/models.py`
- [x] UserRepository with find methods — `src/auth_bc/user/infrastructure/repository.py`
- [x] UserRole enum — `src/auth_bc/user/domain/enums.py`

### Required from E3 (All Exist)

- [x] ServiceRequest entity with status, assigned_to, created_by — `src/request_bc/request/domain/entities.py`
- [x] RequestEvent (append-only audit trail) — already records all mutations
- [x] Request command handlers — 6 handlers that will emit domain events
- [x] RequestRepository — for looking up request details during event enrichment

### New Bounded Context

- `notification_bc` is entirely new — no existing code to conflict with
- ForeignKey references: users.id, companies.id (all exist)
- No FK to service_requests (request_id stored in JSON data field — loose coupling)

---

## Scope Validation

### In Scope (from roadmap)

- [x] WebSocket endpoint (per user, JWT auth)
- [x] Domain events on state changes
- [x] Pub/sub: route events to subscribers (notifier, audit)
- [x] In-app notification storage and read/unread
- [x] Push events: request status changed, comment added, report ready

### Not in Scope (deferred to later epics)

- Email notifications (future subscriber)
- Report-ready notifications (E6 — report generation)
- Dashboard metric updates via WebSocket (E5)
- Redis pub/sub for multi-worker scaling (future optimization)
- Notification preferences/settings per user (future feature)

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| WebSocket adds stateful connections to a stateless API | ConnectionManager is in-memory, scoped to single worker. Graceful degradation — notifications still stored if WS fails |
| Event bus adds coupling to command handlers | Minimal coupling — handlers return events, bus dispatches. Handlers don't know about subscribers |
| Bulk notification creation for many technicians | Use `session.add_all()` for batch insert. Company technician count is bounded (<50 typical) |
| WebSocket JWT expiry during long connection | Check token on connect only. For v1, client reconnects on disconnect. Future: periodic reauth |
| In-memory connection state lost on restart | Acceptable for v1 — clients reconnect automatically. Notifications are persisted regardless |
| Circular dependency: request_bc commands importing notification_bc | Avoid by using event bus at the adapter layer (router), not in domain command handlers |

---

## Observations

### 1. Event Emission Point
Domain events should be emitted at the router/adapter layer AFTER the command handler succeeds, not inside the command handler itself. This avoids coupling the request_bc to the notification_bc. The router calls the command handler, then publishes the event to the event bus.

### 2. Target Resolution Needs User Queries
The TargetResolver needs to find "all technicians in company X" for `request.created` events. This requires querying the UserRepository. Inject UserRepository into the TargetResolver, not into individual subscribers.

### 3. WebSocket Message Format
Keep messages simple and consistent:
```json
{
  "type": "notification",
  "data": {
    "id": "01HXYZ...",
    "event_type": "request.status_changed",
    "title": "Request #ABC updated",
    "body": "Status changed from in_review to in_progress",
    "data": {"request_id": "...", "old_status": "in_review", "new_status": "in_progress"},
    "created_at": "2026-02-15T10:30:00Z"
  }
}
```

### 4. Notification Model — Simple Table
Only one new table: `notifications`. No junction tables, no notification types table. Keep it flat. The `event_type` string field handles categorization.

### 5. Existing CommandBus Has Event Support
`command_bus.py` already has `dispatch_with_events()` and `get_pending_events()` support. However, our current command handlers don't use the CommandBus — they're instantiated directly in routers. For v1, emit events at the router layer. The CommandBus can be integrated later for cleaner architecture.

---

## Estimated Complexity

| Area | Items | Complexity |
|---|---|---|
| Domain entities | 2 (Notification, DomainEvent value object) + 1 enum | Low |
| Repository | 1 interface + 1 implementation | Low-Medium |
| Event bus + subscribers | 3 services (event bus, notification subscriber, WebSocket subscriber) + target resolver | High |
| Commands | 2 (mark_read, mark_all_read) | Low |
| Queries | 1 (list_notifications with unread_count) | Low |
| WebSocket | 1 endpoint + connection manager | Medium |
| Router modifications | Extend my router + 6 request command routers emit events | Medium |
| Migration | 1 table (notifications) | Low |
| Tests | ~40 unit tests + WebSocket integration tests | Medium |

**Overall:** Medium-High. The event bus and WebSocket infrastructure are new patterns for the codebase. Individual components are simple, but the integration across bounded contexts (request_bc emitting events → notification_bc consuming them) adds architectural complexity.

---

## Validation Result

**Status:** APPROVED — Ready for slicing

All E0, E1, and E3 dependencies are in place. WebSocket support is available (websockets package installed). Redis is configured for future pub/sub. The notification_bc is a new, isolated bounded context. Event emission happens at the adapter layer to avoid cross-BC coupling. Follow established patterns for entities, repositories, and HTTP endpoints.
