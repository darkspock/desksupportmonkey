# Tasks: F0 - Request CRUD + State Machine

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create RequestType, RequestStatus, RequestPriority enums
- **File:** `src/request_bc/request/domain/enums.py` (NEW)
- RequestType: incident, new_equipment, onboarding
- RequestStatus: submitted, in_review, in_progress, resolved, rejected
- RequestPriority: low, medium, high, urgent
- VALID_STATUS_TRANSITIONS map
- PRIORITY_SORT_ORDER map (low=1, medium=2, high=3, urgent=4)
- DEFAULT_PRIORITY map (incident=high, new_equipment=low, onboarding=medium)
- InvalidStatusTransitionError class (same pattern as asset_bc)

### T1.2: Create ServiceRequest entity
- **File:** `src/request_bc/request/domain/entities.py` (NEW)
- Dataclass with all fields from design
- `create()`: validates title/description not empty, generates ULID, status=submitted, priority=DEFAULT_PRIORITY[type]
- `change_status()`: validates transition via VALID_STATUS_TRANSITIONS, sets resolved_at if resolved/rejected
- `change_priority()`: updates priority field
- `assign()`: sets assigned_to

### T1.3: Create RequestEvent entity
- Same file as T1.2
- Dataclass: id, request_id, event_type, data (dict), performed_by, created_at
- `create()`: generates ULID

### T1.4: Create RequestComment + RequestNote entities
- Same file as T1.2
- RequestComment: id, request_id, author_id, body, created_at + `create()`
- RequestNote: id, request_id, author_id, body, created_at + `create()`
- Both validate body is not empty

### T1.5: Create RequestRepositoryInterface
- **File:** `src/request_bc/request/domain/repository.py` (NEW)
- ABC with full method signatures from design
- F0 methods: save, find_by_id, save_event, count_comments
- F1 methods: find_all (stub for now)
- F2 methods: save_comment, find_comments, save_note, find_notes
- F3 methods: find_by_created_by

### T1.6: Create __init__.py files
- `src/request_bc/__init__.py`
- `src/request_bc/request/__init__.py`
- `src/request_bc/request/domain/__init__.py`
- `src/request_bc/request/application/__init__.py`
- `src/request_bc/request/application/commands/__init__.py`
- `src/request_bc/request/application/queries/__init__.py`
- `src/request_bc/request/infrastructure/__init__.py`
- `adapters/http/api/requests/__init__.py`

---

## Phase 2: Infrastructure Layer

### T2.1: Create ServiceRequestModel
- **File:** `src/request_bc/request/infrastructure/models.py` (NEW)
- ServiceRequestModel(ULIDMixin, TimestampMixin, Base): all columns from design
- Composite indexes: (company_id, status), (company_id, created_by), (company_id, assigned_to)

### T2.2: Create RequestEventModel
- Same file
- RequestEventModel(ULIDMixin, Base): request_id, event_type, data (JSON), performed_by, created_at
- No TimestampMixin

### T2.3: Create RequestCommentModel + RequestNoteModel
- Same file
- Both: ULIDMixin only, request_id (indexed), author_id, body, created_at
- RequestCommentModel.__tablename__ = "request_comments"
- RequestNoteModel.__tablename__ = "request_notes"

### T2.4: Update models_registry.py
- Add imports for ServiceRequestModel, RequestEventModel, RequestCommentModel, RequestNoteModel

### T2.5: Create Alembic migration
- `alembic revision --autogenerate -m "add_service_requests_and_related_tables"`
- Verify: 4 tables with all indexes, FKs, constraints
- Test upgrade + downgrade

### T2.6: Implement RequestRepository (F0 methods)
- **File:** `src/request_bc/request/infrastructure/repository.py` (NEW)
- save(): upsert pattern (merge + flush + refresh)
- find_by_id(): select by id + company_id
- save_event(): insert event
- count_comments(): select count from request_comments where request_id
- _to_entity(), _event_to_entity() conversions

---

## Phase 3: Application Layer

### T3.1: CreateRequestCommand + Handler
- **File:** `src/request_bc/request/application/commands/create_request.py` (NEW)
- Command: company_id, created_by, type, title, description, data
- Handler: validate type enum, create entity, save, create event, return
- Define no custom errors — ValueError from entity for validation

### T3.2: ChangeRequestStatusCommand + Handler
- **File:** `src/request_bc/request/application/commands/change_request_status.py` (NEW)
- Command: request_id, company_id, new_status, performed_by
- Handler: find -> RequestNotFoundError, change_status (validates transitions), auto-assign side effect, save, create events, return
- Define RequestNotFoundError

### T3.3: ChangeRequestPriorityCommand + Handler
- **File:** `src/request_bc/request/application/commands/change_request_priority.py` (NEW)
- Command: request_id, company_id, new_priority, performed_by
- Handler: find -> RequestNotFoundError, validate priority enum, change_priority, save, create event, return
- Define RequestNotFoundError (or share from T3.2)

### T3.4: GetRequestQuery + Handler
- **File:** `src/request_bc/request/application/queries/get_request.py` (NEW)
- Query: request_id, company_id
- Handler: find -> RequestNotFoundError, get comment_count, return (request, comment_count)

---

## Phase 4: HTTP Layer

### T4.1: Create request schemas
- **File:** `adapters/http/api/requests/schemas.py` (NEW)
- CreateRequestRequest, ChangeStatusRequest, ChangePriorityRequest
- RequestResponse (with comment_count field)

### T4.2: Create request router
- **File:** `adapters/http/api/requests/routers.py` (NEW)
- POST /api/v1/requests -> create_request (employee+, any authenticated user)
- GET /api/v1/requests/{request_id} -> get_request (employee own / technician+)
- PATCH /api/v1/requests/{request_id}/status -> change_status (technician+)
- PATCH /api/v1/requests/{request_id}/priority -> change_priority (technician+)
- Access control: on GET detail, if user role < TECHNICIAN and request.created_by != user.id -> 404
- Error mapping: RequestNotFoundError->404, InvalidStatusTransitionError->409, ValueError->422

### T4.3: Register router in app.py
- Import and include requests router

---

## Phase 5: Tests

### T5.1: Unit tests - Enums
- **File:** `tests/unit/request_bc/request/domain/test_enums.py` (NEW)
- Valid transitions for each status
- Invalid transitions raise error
- Default priority mapping
- Priority sort order

### T5.2: Unit tests - ServiceRequest entity
- **File:** `tests/unit/request_bc/request/domain/test_entities.py` (NEW)
- Create with valid data, priority auto-assigned
- Create with empty title/description raises ValueError
- change_status valid transitions (all 5)
- change_status invalid transition raises
- change_status to resolved sets resolved_at
- change_status to rejected sets resolved_at
- change_priority updates field
- assign sets assigned_to

### T5.3: Unit tests - RequestEvent, RequestComment, RequestNote entities
- Same file or separate
- Create event with data
- Create comment with valid body
- Create comment with empty body raises ValueError
- Create note with valid body
- Create note with empty body raises ValueError

### T5.4: Unit tests - Commands
- **File:** `tests/unit/request_bc/request/application/commands/test_commands.py` (NEW)
- CreateRequest: success with auto-priority, invalid type
- ChangeStatus: success, not found, invalid transition, auto-assign on in_review
- ChangePriority: success, not found, invalid priority

### T5.5: Unit tests - Queries
- **File:** `tests/unit/request_bc/request/application/queries/test_queries.py` (NEW)
- GetRequest: success with comment_count, not found

---

## Phase 6: Verification

### T6.1: Run all tests
### T6.2: Run migration
### T6.3: Manual verification
1. Create incident request -> verify auto-priority=high
2. Create new_equipment request -> verify auto-priority=low
3. Create onboarding request -> verify auto-priority=medium
4. Get request detail -> verify response with comment_count=0
5. Change status submitted->in_review -> verify auto-assign
6. Change status in_review->in_progress -> verify
7. Change status in_progress->resolved -> verify resolved_at set
8. Change status invalid -> 409
9. Change priority -> verify event recorded
10. Employee access own request -> 200
11. Employee access other's request -> 404

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.6 | 3 + inits | -- |
| 2. Infrastructure | T2.1-T2.6 | 2 + migration | 1 (models_registry) |
| 3. Application | T3.1-T3.4 | 4 | -- |
| 4. HTTP | T4.1-T4.3 | 2 + init | 1 (app.py) |
| 5. Tests | T5.1-T5.5 | 4 | -- |
| 6. Verification | T6.1-T6.3 | -- | -- |
