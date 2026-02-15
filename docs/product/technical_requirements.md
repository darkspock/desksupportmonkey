# DeskSupportMonkey - Technical Requirements

See also: [Functional Requirements](functional_requirements.md)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | Python 3.13 + FastAPI |
| **Frontend** | React + TypeScript (Vite) |
| **Database** | PostgreSQL 15 |
| **ORM** | SQLAlchemy + Alembic (migrations) |
| **Queue** | Celery + Redis (async report generation) |
| **Object Storage** | MinIO (S3-compatible, for generated reports) |
| **Real-time** | WebSockets (FastAPI native) |
| **Auth** | Magic link via email, JWT tokens, role-based access |
| **Email (dev)** | Mailpit (fake SMTP for local development) |
| **Package Manager** | uv |
| **Containerization** | Docker Compose (dev environment) |

---

## Architecture

### Overall: DDD + Clean Architecture + CQRS

```
adapters/http/          # HTTP layer (FastAPI routers, DTOs)
src/
├── framework/          # CQRS framework (Command Bus, Query Bus)
├── <module>_bc/        # Bounded contexts (one per business module)
│   ├── <entity>/
│   │   ├── domain/           # Entities, value objects, domain events
│   │   ├── application/      # Commands, queries, handlers
│   │   └── infrastructure/   # Repositories, models, tasks
core/                   # Config, database, Celery, base classes
models/                 # SQLAlchemy model registry
```

### Bounded Contexts

| BC | Domain |
|---|---|
| `auth_bc` | Users, magic links, sessions, roles |
| `company_bc` | Companies, departments, email domains |
| `asset_bc` | Assets, asset history (event sourcing) |
| `request_bc` | Service requests, state machine, comments |
| `notification_bc` | In-app notifications, WebSocket events |
| `reporting_bc` | Report generation (Celery task), S3 storage |

---

## Architectural Patterns (Demo Purpose)

These patterns are intentionally included to showcase architecture during training and consulting demos:

| Pattern | Implementation |
|---|---|
| **Message Queue (Celery)** | Admin requests a report -> Celery task generates it async -> stores PDF in MinIO -> notifies when ready |
| **State Machine** | Request lifecycle: `submitted` -> `in_review` -> `in_progress` -> `resolved` / `rejected`. Transitions validated, invalid transitions blocked |
| **Event-Driven** | State changes emit domain events that trigger side effects (notifications, audit log entries) |
| **WebSockets** | Employee portal receives real-time updates when their request changes status |
| **Pub/Sub** | Domain events routed to multiple subscribers: notifier, audit logger, dashboard updater |
| **CQRS** | Commands (create request, change status) separated from queries (list my requests, dashboard metrics). Different models optimized for each |
| **Event Sourcing** | Asset history stored as append-only event log. Current state derived from events. Full audit trail |
| **RBAC** | Role-based access control: super_admin > admin > technician > employee. Checked at HTTP layer via dependencies |
| **Audit Trail** | Every mutation logged with: who (user_id), what (action + entity), when (timestamp), company context |
| **Multi-tenancy** | All queries scoped by company_id. Data isolation enforced at repository level |

---

## API Design

### REST conventions
- Base path: `/api/v1/`
- Resources: plural nouns (`/assets`, `/requests`, `/companies`)
- Nested resources where ownership is clear: `/companies/{id}/users`
- Standard HTTP methods: GET (list/detail), POST (create), PUT (update), DELETE
- Pagination: `?page=1&page_size=20`
- Filtering: query params (`?status=in_stock&type=laptop`)
- Sorting: `?sort_by=created_at&sort_order=desc`

### Response format
```json
{
  "data": { ... },
  "meta": { "page": 1, "page_size": 20, "total": 150 }
}
```

### Error format
```json
{
  "error": {
    "code": "ASSET_NOT_FOUND",
    "message": "Asset with id '...' not found"
  }
}
```

### Authentication
- `POST /api/v1/auth/magic-link` - Request magic link (email)
- `POST /api/v1/auth/verify` - Verify magic link token, returns JWT
- JWT sent as `Authorization: Bearer <token>` header
- JWT payload: `{ user_id, company_id, role, exp }`

### WebSocket
- Endpoint: `/ws/{company_id}/{user_id}`
- Events pushed: `request.status_changed`, `request.comment_added`, `notification.new`

---

## Database

### Key design decisions
- ULIDs as primary keys (sortable, no sequential guessing)
- All tables include: `id`, `created_at`, `updated_at`
- Company-scoped tables include: `company_id` (foreign key, indexed)
- Soft deletes where needed: `deactivated_at` timestamp (users, companies)
- Asset history: append-only `asset_events` table (event sourcing)

### Multi-tenancy strategy
- Single database, shared schema
- `company_id` column on all tenant-scoped tables
- Repository base class enforces company_id filtering
- Indexes on `(company_id, ...)` for all common queries

---

## Report Generation (Celery + MinIO)

### Flow
1. Admin clicks "Generate Report" in dashboard
2. API creates a `report` record (status: `pending`) and enqueues a Celery task
3. Celery worker picks up the task from the `reports` queue
4. Worker queries data, renders HTML template with Jinja2, converts to PDF with WeasyPrint
5. Worker uploads PDF to MinIO bucket (`dsm-reports`)
6. Worker updates report record (status: `completed`, `s3_key`, `generated_at`)
7. WebSocket notifies admin that report is ready
8. Admin downloads report via signed S3 URL (1 hour expiry)

### Report types
- **Asset Inventory Report** - All assets with current status and assignments
- **Request Summary Report** - Requests by period, type, resolution time
- **Technician Performance Report** - Requests per technician, average resolution time

### Error handling
- Max 3 retries with exponential backoff
- On final failure: report status set to `failed`, admin notified
- Task time limit: 5 minutes

---

## Real-time (WebSockets)

### Events
| Event | Triggered by | Sent to |
|---|---|---|
| `request.status_changed` | Technician changes request status | Request creator |
| `request.comment_added` | Anyone adds a comment | All participants |
| `request.assigned` | Technician claims request | Request creator |
| `notification.new` | Any notable action | Target user |
| `report.ready` | Celery task completes report | Admin who requested it |

### Connection management
- JWT validated on WebSocket connection
- One connection per user session
- Auto-reconnect on frontend with exponential backoff
- Heartbeat ping every 30 seconds

---

## Non-Functional Requirements

### Performance
- API response time < 200ms for list endpoints (p95)
- WebSocket event delivery < 500ms
- Report generation < 60 seconds for standard reports

### Security
- All endpoints require authentication (except magic link request and verify)
- Company data isolation enforced at repository level
- JWT tokens expire after 24 hours (same as magic link)
- Rate limiting on magic link requests (max 5 per email per hour)
- Input validation on all endpoints (Pydantic models)
- No sensitive data in logs

### Development
- Docker Compose for local dev (PostgreSQL + Redis + Mailpit + MinIO)
- Environment-based configuration (`.env` file)
- Seed data script for demos (companies, users, assets, requests in various states)
- Alembic migrations for all schema changes
- Type hints throughout the codebase
- pytest for backend tests

### Observability
- Structured logging (JSON format in production)
- Health check endpoint: `GET /health`
- Celery task status queryable via API
