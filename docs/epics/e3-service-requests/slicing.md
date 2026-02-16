# Slicing: E3 - Service Requests

**Epic:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-02-15

---

## Feature Breakdown

| Feature | Description | User Stories | Complexity | Status |
|---|---|---|---|---|
| **F0** | Request CRUD + State Machine | US-001, US-002, US-003, US-009 | High | Done |
| **F1** | Technician Queue + Assignment | US-004, US-005 | Medium | Done |
| **F2** | Comments + Internal Notes | US-006, US-007 | Medium | Done |
| **F3** | My Requests (Employee) | US-008 | Low | Done |

---

## F0: Request CRUD + State Machine

**Scope:** Core request entity, types/statuses/priorities with state machine, create endpoint, status change endpoint, priority override, request detail, event sourcing infrastructure.

**Why F0:** Everything else depends on ServiceRequest existing. The state machine and event recording must be baked in from the start — same rationale as E2-F0 with asset events.

**Includes:**
- ServiceRequest entity with type, status, priority, state machine
- RequestEvent entity (append-only)
- RequestType, RequestStatus, RequestPriority enums with transitions
- RequestRepositoryInterface + RequestRepository
- Create request command (with auto-priority)
- Change status command (with auto-assign side effect)
- Change priority command
- Get request detail query (with employee access control)
- HTTP router for create + status change + priority change + detail
- Alembic migration (service_requests + request_events tables)
- SQLAlchemy models (ServiceRequestModel, RequestEventModel)
- Models registry update, app.py router registration

**Endpoints:**
- `POST /api/v1/requests` — create request (employee+)
- `GET /api/v1/requests/{id}` — get request detail (employee own / technician+ any)
- `PATCH /api/v1/requests/{id}/status` — change status (technician+)
- `PATCH /api/v1/requests/{id}/priority` — change priority (technician+)

---

## F1: Technician Queue + Assignment

**Scope:** List requests with search/filter/sort, assign/claim requests.

**Why F1:** The queue is the technician's primary workspace. Assignment connects requests to specific technicians. Must come before comments/notes since technicians need to find requests first.

**Depends on:** F0 (ServiceRequest entity and repository must exist)

**Includes:**
- List requests query with filters (status, type, priority, assigned_to, search)
- Sort by priority desc + created_at asc (default queue ordering)
- Assign request command (claim/reassign)
- HTTP endpoints for list + assign

**Endpoints:**
- `GET /api/v1/requests` — list/search requests (technician+)
- `PATCH /api/v1/requests/{id}/assign` — assign to technician (technician+)

---

## F2: Comments + Internal Notes

**Scope:** Public comments (employee + technician) and private internal notes (technician only).

**Why F2:** Communication between employee and technician is critical for request resolution. Internal notes allow technicians to record technical details privately.

**Depends on:** F0 (ServiceRequest must exist)

**Includes:**
- RequestComment entity + RequestNoteModel
- RequestNote entity + RequestNoteModel
- Add comment command + add note command
- List comments query + list notes query
- Comment/note events recorded in RequestEvent
- HTTP endpoints for CRUD
- Alembic migration (request_comments + request_notes tables)

**Endpoints:**
- `POST /api/v1/requests/{id}/comments` — add comment (employee own / technician+)
- `GET /api/v1/requests/{id}/comments` — list comments (employee own / technician+)
- `POST /api/v1/requests/{id}/notes` — add internal note (technician+)
- `GET /api/v1/requests/{id}/notes` — list internal notes (technician+)

---

## F3: My Requests (Employee)

**Scope:** Employee-facing view of their own submitted requests.

**Why F3:** Last because it's a simple read-only query on top of F0's data. Low complexity, high value for employees.

**Depends on:** F0 (ServiceRequest must exist), F1 (nice to have queue filters pattern to reuse)

**Includes:**
- My Requests query (filter by created_by = current user)
- Filter by status
- Pagination, default sort created_at desc
- Extend my router with new endpoint
- Extend my schemas

**Endpoints:**
- `GET /api/v1/my/requests` — list my requests (employee+)

---

## Dependency Graph

```
F0: Request CRUD + State Machine
 │
 ├── F1: Technician Queue + Assignment
 │
 ├── F2: Comments + Internal Notes
 │
 └── F3: My Requests (Employee)
```

F1, F2, and F3 all depend on F0 but are independent of each other. However, recommended order is F0 → F1 → F2 → F3 because:
- F1 establishes the list/filter pattern that F3 reuses
- F2 adds the comment_count field that enhances request detail from F0
- F3 is simplest and benefits from all prior patterns

---

## Implementation Order

1. **F0** — Request CRUD + State Machine (foundation + migration)
2. **F1** — Technician Queue + Assignment (primary workflow)
3. **F2** — Comments + Internal Notes (communication layer)
4. **F3** — My Requests (employee view)

---

## Migration Strategy

**Single migration for all 4 tables** (created in F0, extended in F2):
- Option A: One migration in F0 with all 4 tables upfront
- Option B: F0 creates service_requests + request_events, F2 creates request_comments + request_notes

**Recommend Option A:** Create all 4 tables in F0's migration. The tables are simple and well-defined. This avoids migration ordering issues and lets F2 focus purely on application logic.
