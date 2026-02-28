# Implementation Tasks: Change Request CRUD + State Machine + List/Detail Pages

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-27
**Total Tasks:** 28
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Repository Interface | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Migration | 1 | S |
| Infrastructure - Repository | 1 | M |
| Application - Commands | 10 | M |
| Application - Queries | 2 | M |
| HTTP - Schemas | 1 | S |
| HTTP - Dependencies | 1 | S |
| HTTP - Router | 1 | L |
| Notifications | 1 | S |
| Config | 1 | S |
| Tests - Unit (Domain) | 1 | M |
| Tests - Unit (Commands + Queries) | 1 | L |
| Tests - Integration | 1 | L |
| Frontend - ChangeListPage | 1 | M |
| Frontend - ChangeDetailPage | 1 | L |
| Frontend - Config (router, nav, i18n, types) | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create domain enums

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**File:** `src/change_bc/change_request/domain/enums.py`

**Description:**
Create all domain enums for the change_bc bounded context.

**Implementation:**
- `ChangeType(str, Enum)` — `STANDARD = "standard"`, `NORMAL = "normal"`, `EMERGENCY = "emergency"`
- `ChangeStatus(str, Enum)` — 8 values: `DRAFT`, `PENDING_APPROVAL`, `SCHEDULED`, `IN_PROGRESS`, `IMPLEMENTED`, `CLOSED`, `REJECTED`, `ROLLED_BACK`
  - `@property is_terminal` → True for CLOSED, REJECTED, ROLLED_BACK
- `VALID_TRANSITIONS: dict[ChangeStatus, list[ChangeStatus]]` — state machine rules as defined in design
- `ChangeEventType(str, Enum)` — 10 values: `CREATED`, `UPDATED`, `SUBMITTED`, `APPROVED`, `REJECTED`, `STARTED`, `IMPLEMENTED`, `ROLLED_BACK`, `CLOSED`, `ASSIGNED`
- `InvalidStatusTransitionError(Exception)` — with `current` and `target` attributes, message `f"Cannot transition from {current.value} to {target.value}"`

**Acceptance Criteria:**
- [x] ChangeType has 3 values (standard, normal, emergency)
- [x] ChangeStatus has 8 values with is_terminal property
- [x] VALID_TRANSITIONS covers all 8 statuses
- [x] ChangeEventType has 10 values
- [x] InvalidStatusTransitionError stores current and target

---

### TASK-002: Create domain exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**File:** `src/change_bc/change_request/domain/exceptions.py`

**Description:**
Create all domain-specific exceptions.

**Implementation:**
```python
class ChangeNotFoundError(Exception): ...
class ChangeNotEditableError(Exception): ...
class RollbackPlanRequiredError(Exception): ...
class RejectionReasonRequiredError(Exception): ...
class RollbackReasonRequiredError(Exception): ...
class UnauthorizedApprovalError(Exception): ...
```

Note: `InvalidStatusTransitionError` is in `enums.py` (co-located with the state machine).

**Acceptance Criteria:**
- [x] All 6 exception classes created
- [x] Each has a descriptive default message

---

### TASK-003: Create domain entities

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**File:** `src/change_bc/change_request/domain/entities.py`

**Description:**
Create ChangeRequest aggregate root and ChangeEvent audit trail entity.

**ChangeRequest fields:**
`id`, `company_id`, `title`, `description`, `change_type`, `status`, `business_justification`, `risk_assessment`, `rollback_plan`, `planned_date`, `requested_by`, `assigned_to`, `approved_by`, `approved_at`, `rejected_by`, `rejected_at`, `rejection_reason`, `started_at`, `implemented_at`, `implementation_notes`, `rolled_back_at`, `rollback_reason`, `closed_at`, `created_at`, `updated_at`

**ChangeRequest methods:**
- `create(cls, ...)` — factory method, validates title required, sets status=DRAFT, generates ULID
- `_transition(self, target)` — validates via VALID_TRANSITIONS, raises InvalidStatusTransitionError
- `submit(self)` — standard→SCHEDULED, normal/emergency→PENDING_APPROVAL; validates rollback_plan for normal/emergency (raises RollbackPlanRequiredError)
- `approve(self, approved_by)` — PENDING_APPROVAL→SCHEDULED, records approved_by/approved_at
- `reject(self, rejected_by, reason)` — PENDING_APPROVAL→REJECTED, reason required (raises RejectionReasonRequiredError), records fields
- `start(self)` — SCHEDULED→IN_PROGRESS, records started_at
- `implement(self, notes=None)` — IN_PROGRESS→IMPLEMENTED, records implemented_at/implementation_notes
- `rollback(self, reason)` — IN_PROGRESS/IMPLEMENTED→ROLLED_BACK, reason required (raises RollbackReasonRequiredError), records fields
- `close(self)` — IMPLEMENTED→CLOSED, records closed_at
- `update_details(self, ...)` — only in DRAFT/PENDING_APPROVAL (raises ChangeNotEditableError), updates title/description/change_type/business_justification/risk_assessment/rollback_plan/planned_date
- `assign(self, user_id)` — any non-terminal state, sets assigned_to

**ChangeEvent fields:**
`id`, `change_request_id`, `event_type`, `description`, `actor_id`, `created_at`, `metadata`

**ChangeEvent methods:**
- `create(cls, ...)` — factory method, generates ULID

**Acceptance Criteria:**
- [x] ChangeRequest @dataclass with all fields
- [x] create() validates title, sets DRAFT, generates ULID
- [x] _transition() validates via VALID_TRANSITIONS
- [x] submit() auto-approves standard, requires rollback_plan for normal/emergency
- [x] approve() records approved_by and approved_at
- [x] reject() requires reason, records rejected_by/rejected_at/rejection_reason
- [x] start() records started_at
- [x] implement() records implemented_at and optional notes
- [x] rollback() requires reason, records rolled_back_at/rollback_reason
- [x] close() records closed_at
- [x] update_details() only in DRAFT/PENDING_APPROVAL
- [x] assign() works in any non-terminal state
- [x] ChangeEvent @dataclass with create() factory

---

### TASK-004: Create repository interface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/change_bc/change_request/domain/repository.py`

**Description:**
Create the repository interface (port) and filters dataclass.

**Implementation:**
- `ChangeRequestFilters` @dataclass — page, page_size, status, change_type, assigned_to, search, date_from, date_to
- `ChangeRequestRepositoryInterface(ABC)`:
  - `save(change: ChangeRequest) -> None`
  - `find_by_id(change_id: str, company_id: str) -> Optional[ChangeRequest]`
  - `find_all(company_id: str, filters: ChangeRequestFilters) -> tuple[list[ChangeRequest], int]`
  - `save_event(event: ChangeEvent) -> None`
  - `find_events(change_request_id: str) -> list[ChangeEvent]`

**Acceptance Criteria:**
- [x] ChangeRequestFilters with all filter fields
- [x] ABC interface with 5 abstract methods
- [x] Signatures match design exactly

---

## Phase 2: Infrastructure Layer

### TASK-005: Create SQLAlchemy models

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/change_bc/change_request/infrastructure/models.py`

**Description:**
Create ChangeRequestModel and ChangeEventModel using Mapped[] annotations (SQLAlchemy 2.0 style).

**ChangeRequestModel:**
- Inherits ULIDMixin, TimestampMixin, Base
- `__tablename__ = "change_requests"`
- All columns from design with proper types (String, Text, DateTime(timezone=True))
- Composite indexes: `(company_id, status)`, `(company_id, change_type)`, `(planned_date)`

**ChangeEventModel:**
- Inherits ULIDMixin, Base (no TimestampMixin — has its own created_at)
- `__tablename__ = "change_events"`
- FK to change_requests.id
- `metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)`

**Acceptance Criteria:**
- [x] ChangeRequestModel with all columns, Mapped[] annotations
- [x] ChangeEventModel with FK and JSON metadata
- [x] All 3 composite indexes defined
- [x] server_default="draft" for status

---

### TASK-006: Create Alembic migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**File:** `alembic/versions/e33a1_create_change_request_tables.py`

**Description:**
Create migration for change_requests and change_events tables. Schema matches design exactly.

**Acceptance Criteria:**
- [x] change_requests table with all columns
- [x] change_events table with FK to change_requests
- [x] All indexes created
- [x] Reversible (downgrade drops both tables)

---

### TASK-007: Create repository implementation

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-004, TASK-005

**File:** `src/change_bc/change_request/infrastructure/repository.py`

**Description:**
Implement ChangeRequestRepositoryInterface.

**Methods:**
- `save(change)` — insert or update (check by id), flush()
- `find_by_id(change_id, company_id)` — select with company_id filter, return entity or None
- `find_all(company_id, filters)` — paginated query with conditional filters (status, change_type, assigned_to, search on title, date_from/date_to on planned_date), returns (items, total)
- `save_event(event)` — insert ChangeEventModel, flush()
- `find_events(change_request_id)` — select ordered by created_at asc
- `_to_entity(model)` — static, ORM model → ChangeRequest domain entity (enum conversion)
- `_to_event_entity(model)` — static, ORM model → ChangeEvent domain entity

**Acceptance Criteria:**
- [x] Implements ChangeRequestRepositoryInterface
- [x] save() handles insert and update
- [x] find_all() applies all filters conditionally
- [x] find_all() returns correct total count
- [x] Pagination: offset/limit pattern
- [x] _to_entity() converts status/change_type strings to enums
- [x] _to_event_entity() converts event_type string to enum, metadata_json → metadata

---

## Phase 3: Application Layer — Commands

### TASK-008: Create CreateChangeRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/create_change_request.py`

**Description:**
Command + handler to create a change request in DRAFT status. Modal creation: only essential fields (title, type, planned_date).

**Command fields:** change_id, company_id, requested_by, title, change_type (default "standard"), planned_date (optional)

**Handler:** Creates ChangeRequest via factory, saves entity, saves CREATED event.

**Acceptance Criteria:**
- [x] Command inherits from Command
- [x] Handler inherits from CommandHandler[CreateChangeRequestCommand]
- [x] handle() returns None
- [x] Creates entity in DRAFT status
- [x] Records CREATED ChangeEvent

---

### TASK-009: Create UpdateChangeRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/update_change_request.py`

**Description:**
Command + handler to update change request fields. Only allowed in DRAFT/PENDING_APPROVAL.

**Command fields:** change_id, company_id, performed_by, title (opt), description (opt), change_type (opt), business_justification (opt), risk_assessment (opt), rollback_plan (opt), planned_date (opt)

**Handler:** Loads entity, calls update_details(), saves, records UPDATED event.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Raises ChangeNotEditableError if not in DRAFT/PENDING_APPROVAL
- [x] Only updates provided (non-None) fields
- [x] Records UPDATED ChangeEvent

---

### TASK-010: Create SubmitChangeRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/submit_change_request.py`

**Description:**
Command + handler to submit a change for approval. Standard auto-approves to SCHEDULED; normal/emergency go to PENDING_APPROVAL.

**Command fields:** change_id, company_id, performed_by

**Handler:** Loads entity, calls submit(), saves, records SUBMITTED event with metadata `{"auto_approved": bool}`.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Standard type transitions to SCHEDULED
- [x] Normal/emergency transitions to PENDING_APPROVAL
- [x] Raises RollbackPlanRequiredError for normal/emergency without rollback_plan
- [x] Records SUBMITTED event with auto_approved metadata

---

### TASK-011: Create ApproveChangeRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/approve_change_request.py`

**Description:**
Command + handler to approve a pending change. Admin only.

**Command fields:** change_id, company_id, performed_by, performed_by_role, notes (optional)

**Handler:** Loads entity, validates admin role, calls approve(), saves, records APPROVED event with optional notes metadata.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Raises UnauthorizedApprovalError if not admin/super_admin
- [x] Transitions PENDING_APPROVAL → SCHEDULED
- [x] Records APPROVED event with notes metadata if provided

---

### TASK-012: Create RejectChangeRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/reject_change_request.py`

**Description:**
Command + handler to reject a pending change. Admin only, reason mandatory.

**Command fields:** change_id, company_id, performed_by, performed_by_role, reason

**Handler:** Loads entity, validates admin role, calls reject(), saves, records REJECTED event with reason metadata.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Raises UnauthorizedApprovalError if not admin/super_admin
- [x] Raises RejectionReasonRequiredError if reason empty
- [x] Transitions PENDING_APPROVAL → REJECTED
- [x] Records REJECTED event with reason metadata

---

### TASK-013: Create StartChangeCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/start_change.py`

**Description:**
Command + handler to start implementing a scheduled change.

**Command fields:** change_id, company_id, performed_by

**Handler:** Loads entity, calls start(), saves, records STARTED event.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Transitions SCHEDULED → IN_PROGRESS
- [x] Records STARTED event

---

### TASK-014: Create ImplementChangeCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/implement_change.py`

**Description:**
Command + handler to mark a change as implemented.

**Command fields:** change_id, company_id, performed_by, notes (optional)

**Handler:** Loads entity, calls implement(notes), saves, records IMPLEMENTED event with notes metadata.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Transitions IN_PROGRESS → IMPLEMENTED
- [x] Records IMPLEMENTED event with optional notes

---

### TASK-015: Create RollbackChangeCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/rollback_change.py`

**Description:**
Command + handler to roll back a change. Reason mandatory.

**Command fields:** change_id, company_id, performed_by, reason

**Handler:** Loads entity, calls rollback(reason), saves, records ROLLED_BACK event with reason metadata.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Raises RollbackReasonRequiredError if reason empty
- [x] Transitions IN_PROGRESS or IMPLEMENTED → ROLLED_BACK
- [x] Records ROLLED_BACK event with reason metadata

---

### TASK-016: Create CloseChangeCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/close_change.py`

**Description:**
Command + handler to close an implemented change. Admin only.

**Command fields:** change_id, company_id, performed_by, performed_by_role

**Handler:** Loads entity, validates admin role, calls close(), saves, records CLOSED event.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Validates admin/super_admin role
- [x] Transitions IMPLEMENTED → CLOSED
- [x] Records CLOSED event

---

### TASK-017: Create AssignChangeCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/commands/assign_change.py`

**Description:**
Command + handler to assign a technician to a change. Allowed in any non-terminal state.

**Command fields:** change_id, company_id, performed_by, assigned_to

**Handler:** Loads entity, calls assign(assigned_to), saves, records ASSIGNED event with assigned_to metadata.

**Acceptance Criteria:**
- [x] Raises ChangeNotFoundError if not found
- [x] Assigns in any non-terminal state
- [x] Records ASSIGNED event with assigned_to metadata

---

## Phase 3: Application Layer — Queries

### TASK-018: Create ListChangeRequestsQuery

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/queries/list_change_requests.py`

**Description:**
Query + handler + DTO for listing change requests with pagination and filters.

**Contains:**
- `ChangeRequestListDto` @dataclass — id, title, change_type, status, planned_date, assigned_to, assigned_to_name, requested_by, requested_by_name, created_at, updated_at
- `ListChangeRequestsQuery(Query)` — company_id, page, page_size, status, change_type, assigned_to, search, date_from, date_to
- `ListChangeRequestsQueryHandler(QueryHandler[..., tuple[list[ChangeRequestListDto], int]])` — uses user_name_resolver for batch name resolution

**Acceptance Criteria:**
- [x] Query inherits from Query
- [x] Handler inherits from QueryHandler with correct generics
- [x] Batch resolves user names (no N+1)
- [x] Returns DTOs, not entities

---

### TASK-019: Create GetChangeRequestDetailQuery

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004

**File:** `src/change_bc/change_request/application/queries/get_change_request_detail.py`

**Description:**
Query + handler + DTOs for getting change request detail with timeline.

**Contains:**
- `ChangeEventDto` @dataclass — id, event_type, description, actor_id, actor_name, created_at, metadata
- `ChangeRequestDetailDto` @dataclass — all entity fields + resolved names + `timeline: list[ChangeEventDto]`
- `GetChangeRequestDetailQuery(Query)` — change_id, company_id
- `GetChangeRequestDetailQueryHandler(QueryHandler[..., Optional[ChangeRequestDetailDto]])` — loads entity + events, batch resolves names

**Acceptance Criteria:**
- [x] Returns None if change not found
- [x] Includes timeline events ordered by created_at
- [x] Batch resolves all user names (requested_by, assigned_to, approved_by, rejected_by, event actors)
- [x] Returns DTO, not entity

---

## Phase 4: HTTP Layer

### TASK-020: Create Pydantic schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**File:** `adapters/http/api/changes/schemas.py`

**Description:**
Create all request and response Pydantic schemas.

**Request schemas:**
- `CreateChangeRequestSchema` — title (required, 1-255), change_type (default "standard"), planned_date (optional)
- `UpdateChangeRequestSchema` — all fields optional: title, description, change_type, business_justification, risk_assessment, rollback_plan, planned_date
- `ApproveChangeRequestSchema` — notes (optional)
- `RejectChangeRequestSchema` — reason (required, min_length=1)
- `ImplementChangeSchema` — notes (optional)
- `RollbackChangeSchema` — reason (required, min_length=1)
- `AssignChangeSchema` — assigned_to (required)

**Response schemas:**
- `ChangeRequestListItemResponse` — list item fields
- `ChangeEventResponse` — event fields
- `ChangeRequestDetailResponse` — all detail fields + `timeline: list[ChangeEventResponse]`

**Acceptance Criteria:**
- [x] All request schemas with correct validation
- [x] All response schemas matching DTOs
- [x] Field validation (min_length, max_length) on required text fields

---

### TASK-021: Create dependencies

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-007

**File:** `adapters/http/api/changes/dependencies.py`

**Description:**
Create FastAPI dependency functions.

**Functions:**
- `get_change_repo(db) -> ChangeRequestRepository`
- `get_user_repo(db) -> UserRepository`

**Acceptance Criteria:**
- [x] Both functions use Depends(get_db) for session injection
- [x] Return concrete repository instances

---

### TASK-022: Create router with all endpoints

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-008 through TASK-019, TASK-020, TASK-021

**File:** `adapters/http/api/changes/routers.py`

**Description:**
Create router with all 12 endpoints. Direct handler instantiation pattern (no controller).

**Endpoints:**
| Method | Route | Function | Auth |
|--------|-------|----------|------|
| POST | `` | create_change_request | technician+ |
| GET | `` | list_change_requests | technician+ |
| GET | `/{change_id}` | get_change_request | technician+ |
| PATCH | `/{change_id}` | update_change_request | technician+ |
| POST | `/{change_id}/submit` | submit_change_request | technician+ |
| POST | `/{change_id}/approve` | approve_change_request | admin+ |
| POST | `/{change_id}/reject` | reject_change_request | admin+ |
| POST | `/{change_id}/start` | start_change | technician+ |
| POST | `/{change_id}/implement` | implement_change | technician+ |
| POST | `/{change_id}/rollback` | rollback_change | technician+ |
| POST | `/{change_id}/close` | close_change | admin+ |
| POST | `/{change_id}/assign` | assign_change | admin+ |

**Pattern per endpoint:**
1. Inject repos via Depends
2. Instantiate handler inline
3. Build command/query from request + current_user
4. Call handler.handle()
5. For commands: db.commit() after handle, then return detail via query handler
6. Catch domain exceptions → HTTPException mapping
7. For list: return `{"data": [...], "meta": PaginationMeta(...)}`

**Exception mapping:**
- ChangeNotFoundError → 404
- InvalidStatusTransitionError → 422
- ChangeNotEditableError → 422
- RollbackPlanRequiredError → 422
- RejectionReasonRequiredError → 422
- RollbackReasonRequiredError → 422
- UnauthorizedApprovalError → 403
- ValueError → 422

**Helper:** `_user_name_resolver_factory(user_repo)` — same pattern as incident router

**Acceptance Criteria:**
- [x] All 12 endpoints implemented
- [x] Correct auth roles per endpoint
- [x] All domain exceptions caught and mapped to HTTP errors
- [x] Create returns 201, all others 200
- [x] List returns paginated response with meta
- [x] Detail includes timeline

---

## Phase 5: Notifications

### TASK-023: Wire approve/reject notifications

**Phase:** Notifications
**Complexity:** S
**Dependencies:** TASK-022

**Description:**
Add notification events for change approved and rejected.

**Files to modify/create:**
1. `src/notification_bc/notification/domain/enums.py` — Add `CHANGE_APPROVED = "change_approved"` and `CHANGE_REJECTED = "change_rejected"` to EventType
2. `src/change_bc/change_request/application/services/__init__.py` — empty
3. `src/change_bc/change_request/application/services/event_factory.py` — Create ChangeEventFactory with `change_approved()` and `change_rejected()` static methods (following VulnerabilityEventFactory pattern). Include `requested_by` in payload.
4. `src/notification_bc/notification/application/services/target_resolver.py` — Add `_resolve_change_requester()` method, map both event types to it. Resolves to `{payload["requested_by"]}`.
5. `adapters/http/api/changes/routers.py` — In approve and reject endpoints, add `db` and `event_bus` dependencies, publish notification after db.commit()
6. `tests/unit/notification_bc/notification/domain/test_entities.py` — Update EventType count (51 → 53)

**Acceptance Criteria:**
- [x] 2 new EventType entries
- [x] ChangeEventFactory creates DomainEvents with correct payloads
- [x] TargetResolver resolves to the change requester
- [x] Approve route publishes CHANGE_APPROVED notification
- [x] Reject route publishes CHANGE_REJECTED notification
- [x] EventType count test updated

---

## Phase 6: Configuration

### TASK-024: Register router and create __init__.py files

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-022

**Description:**
Register the changes router in app.py and create all __init__.py files.

**Files:**
1. `app.py` — Add `from adapters.http.api.changes.routers import router as changes_router` and `app.include_router(changes_router)`
2. Create empty `__init__.py` in:
   - `src/change_bc/__init__.py`
   - `src/change_bc/change_request/__init__.py`
   - `src/change_bc/change_request/domain/__init__.py`
   - `src/change_bc/change_request/application/__init__.py`
   - `src/change_bc/change_request/application/commands/__init__.py`
   - `src/change_bc/change_request/application/queries/__init__.py`
   - `src/change_bc/change_request/application/services/__init__.py`
   - `src/change_bc/change_request/infrastructure/__init__.py`
   - `adapters/http/api/changes/__init__.py`

**Acceptance Criteria:**
- [x] Router registered in app.py
- [x] All __init__.py files created
- [x] Server starts without import errors

---

## Phase 7: Tests

### TASK-025: Unit tests — domain layer

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001, TASK-002, TASK-003

**Files:**
- `tests/unit/change_bc/change_request/domain/test_enums.py`
- `tests/unit/change_bc/change_request/domain/test_entities.py`

**Description:**
Unit tests for domain enums and entities.

**test_enums.py:**
- ChangeType has 3 values
- ChangeStatus has 8 values
- is_terminal returns True for CLOSED, REJECTED, ROLLED_BACK
- is_terminal returns False for non-terminal states
- VALID_TRANSITIONS covers all 8 statuses
- ChangeEventType has 10 values

**test_entities.py — ChangeRequest:**
- create() sets DRAFT status
- create() generates ULID id
- create() validates title required (ValueError on empty)
- submit() standard → SCHEDULED
- submit() normal → PENDING_APPROVAL
- submit() emergency → PENDING_APPROVAL
- submit() requires rollback_plan for normal (RollbackPlanRequiredError)
- submit() requires rollback_plan for emergency (RollbackPlanRequiredError)
- submit() from non-DRAFT raises InvalidStatusTransitionError
- approve() PENDING_APPROVAL → SCHEDULED, sets approved_by/approved_at
- approve() from non-PENDING_APPROVAL raises InvalidStatusTransitionError
- reject() PENDING_APPROVAL → REJECTED, sets fields
- reject() requires reason (RejectionReasonRequiredError)
- start() SCHEDULED → IN_PROGRESS, sets started_at
- implement() IN_PROGRESS → IMPLEMENTED, sets fields
- rollback() IN_PROGRESS → ROLLED_BACK
- rollback() IMPLEMENTED → ROLLED_BACK
- rollback() requires reason (RollbackReasonRequiredError)
- close() IMPLEMENTED → CLOSED, sets closed_at
- update_details() works in DRAFT
- update_details() works in PENDING_APPROVAL
- update_details() raises ChangeNotEditableError in SCHEDULED
- assign() works in non-terminal states
- assign() raises error in terminal state

**test_entities.py — ChangeEvent:**
- create() generates ULID
- create() stores all fields

**Acceptance Criteria:**
- [x] All state transitions tested (valid and invalid)
- [x] All validation rules tested
- [x] All domain exceptions verified
- [x] Tests pass with `make test`

---

### TASK-026: Unit tests — commands and queries

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-008 through TASK-019

**Files:**
- `tests/unit/change_bc/change_request/application/commands/test_create_change_request.py`
- `tests/unit/change_bc/change_request/application/commands/test_update_change_request.py`
- `tests/unit/change_bc/change_request/application/commands/test_submit_change_request.py`
- `tests/unit/change_bc/change_request/application/commands/test_approve_change_request.py`
- `tests/unit/change_bc/change_request/application/commands/test_reject_change_request.py`
- `tests/unit/change_bc/change_request/application/commands/test_start_change.py`
- `tests/unit/change_bc/change_request/application/commands/test_implement_change.py`
- `tests/unit/change_bc/change_request/application/commands/test_rollback_change.py`
- `tests/unit/change_bc/change_request/application/commands/test_close_change.py`
- `tests/unit/change_bc/change_request/application/commands/test_assign_change.py`
- `tests/unit/change_bc/change_request/application/queries/test_list_change_requests.py`
- `tests/unit/change_bc/change_request/application/queries/test_get_change_request_detail.py`

**Description:**
Unit tests for all command and query handlers using MagicMock for repositories.

**Per command test file:**
- Happy path: handler executes successfully, repo.save() called, repo.save_event() called
- Not found: raises ChangeNotFoundError
- Invalid state: raises appropriate exception
- Authorization (where applicable): raises UnauthorizedApprovalError

**Per query test file:**
- Returns correct DTO structure
- Handles empty results
- User name resolution works
- User name resolution handles missing resolver

**Acceptance Criteria:**
- [x] All 10 command handlers tested (happy + error paths)
- [x] Both query handlers tested
- [x] Uses MagicMock for repositories
- [x] Tests pass with `make test`

---

### TASK-027: Integration tests — HTTP endpoints

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-022, TASK-024

**File:** `tests/integration/test_change_request_endpoints.py`

**Description:**
Integration tests for all HTTP endpoints using TestClient and real PostgreSQL.

**Tests:**
- POST /changes — create change request (201)
- GET /changes — list with pagination
- GET /changes — list with status filter
- GET /changes — list with type filter
- GET /changes — list with search
- GET /changes/{id} — detail with timeline
- GET /changes/{id} — 404 for non-existent
- PATCH /changes/{id} — update fields in DRAFT
- PATCH /changes/{id} — 422 when editing in non-editable state
- POST /changes/{id}/submit — submit standard (auto-approve)
- POST /changes/{id}/submit — submit normal (pending)
- POST /changes/{id}/submit — 422 without rollback plan for normal
- POST /changes/{id}/approve — admin approves
- POST /changes/{id}/approve — 403 for non-admin
- POST /changes/{id}/reject — with reason
- POST /changes/{id}/reject — 422 without reason
- POST /changes/{id}/start — scheduled → in_progress
- POST /changes/{id}/implement — with optional notes
- POST /changes/{id}/rollback — with reason
- POST /changes/{id}/close — admin closes
- POST /changes/{id}/assign — assign technician
- Invalid state transitions return 422
- Multi-tenant isolation (company_id)

**Acceptance Criteria:**
- [x] All 12 endpoints tested
- [x] Happy and error paths covered
- [x] Auth roles verified (admin vs technician)
- [x] State transition errors verified
- [x] Tests pass with `make test-integration`

---

## Phase 8: Frontend

### TASK-028: Create ChangeListPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-022

**File:** `web/app/src/pages/admin/ChangeListPage.tsx`

**Description:**
List page with filters, paginated table, and creation modal.

**Components:**
- Filter bar: status dropdown, type dropdown, search input
- Table columns: title (link to detail), type badge, status badge (minimalista colors), planned_date, assigned_to name, created_at
- Pagination component
- "New Change Request" button → opens creation modal
- Creation modal: title (required), change_type (dropdown: standard/normal/emergency), planned_date (date picker)
- useQuery with `['changes', page, status, type, search]`
- useMutation for create, on success navigate to detail page

**Badge color scheme (minimalista):**
- Grey: `draft`
- Blue: `pending_approval`, `scheduled`, `in_progress`, `implemented`
- Green: `closed`
- Red: `rejected`, `rolled_back`

**Acceptance Criteria:**
- [x] Table displays change requests with pagination
- [x] Filters work (status, type, search)
- [x] Creation modal with title, type, planned_date
- [x] Navigates to detail after creation
- [x] Badge colors match minimalista scheme
- [x] Loading/error/empty states handled

---

### TASK-029: Create ChangeDetailPage

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-022

**File:** `web/app/src/pages/admin/ChangeDetailPage.tsx`

**Description:**
Detail page with all fields, visual timeline, and action modals.

**Sections:**
1. **Header:** Title, status badge (minimalista), type badge, assigned_to
2. **Details card:** description, business_justification, risk_assessment, rollback_plan, planned_date, requested_by, timestamps
3. **Action buttons** (conditional per status/role):
   - DRAFT: Submit, Edit, Assign
   - PENDING_APPROVAL: Approve (admin), Reject (admin), Edit, Assign
   - SCHEDULED: Start, Assign
   - IN_PROGRESS: Implement, Rollback, Assign
   - IMPLEMENTED: Close (admin), Rollback, Assign
   - Terminal: no buttons
4. **Visual timeline:** Vertical connector line, icons per event type, color accents, actor name, timestamp, description
5. **Edit mode:** Inline editing for title, description, change_type, business_justification, risk_assessment, rollback_plan, planned_date (only DRAFT/PENDING_APPROVAL)

**Modals:**
- Approve modal: optional notes textarea
- Reject modal: required reason textarea
- Implement modal: optional notes textarea
- Rollback modal: required reason textarea
- Assign modal: user picker (assigned_to)

**Mutations:** useMutation for each action, invalidateQueries on success, showToast on success/error

**Acceptance Criteria:**
- [x] All fields displayed
- [x] Action buttons conditional on status + role
- [x] Approve modal with optional notes
- [x] Reject modal with required reason
- [x] Rollback modal with required reason
- [x] Visual timeline with connector line, icons, colors
- [x] Edit mode for DRAFT/PENDING_APPROVAL
- [x] All mutations work with cache invalidation

---

### TASK-030: Frontend configuration (router, nav, i18n, types)

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-028, TASK-029

**Files:**
- `web/app/src/router.tsx` — Add lazy imports and routes for `/changes` and `/changes/:id`
- `web/app/src/config/navSections.ts` — Add `{ to: '/changes', labelKey: 'nav.changes', roles: ['technician', 'admin', 'super_admin'] }` to **Management** section
- `web/app/src/locales/en.ts` — Add all i18n keys (nav, enums, pages, detail, event types) as specified in design
- `web/app/src/locales/es.ts` — Add Spanish translations for all keys
- `web/app/src/types/index.ts` — Add ChangeRequest, ChangeEvent TypeScript interfaces

**Acceptance Criteria:**
- [x] Routes registered, lazy loaded
- [x] Nav entry in Management section
- [x] All i18n keys in EN and ES
- [x] TypeScript types for API responses
- [x] `npx tsc --noEmit` passes

---

## Dependency Graph

```
TASK-001 (Enums)
    │
    ├── TASK-002 (Exceptions)
    │       │
    │       └── TASK-003 (Entities) ──── TASK-025 (Unit: Domain)
    │               │
    │               ├── TASK-004 (Repo Interface)
    │               │       │
    │               │       ├── TASK-008..017 (Commands) ──┐
    │               │       │                               │
    │               │       ├── TASK-018..019 (Queries) ───┤── TASK-026 (Unit: App)
    │               │       │                               │
    │               │       └── TASK-007 (Repo Impl) ──────┘
    │               │               │
    │               │               └── TASK-021 (Dependencies)
    │               │
    │               └── TASK-005 (Models)
    │                       │
    │                       └── TASK-006 (Migration)
    │
    └── TASK-020 (Schemas) ── no dependencies

TASK-022 (Router) ← TASK-008..021
    │
    ├── TASK-023 (Notifications)
    ├── TASK-024 (Config)
    ├── TASK-027 (Integration Tests)
    ├── TASK-028 (ChangeListPage)
    ├── TASK-029 (ChangeDetailPage)
    └── TASK-030 (Frontend Config) ← TASK-028, TASK-029
```

## Execution Order

**Batch 1 (Parallel):** TASK-001 (Enums), TASK-020 (Schemas)
**Batch 2 (Sequential):** TASK-002 (Exceptions) → TASK-003 (Entities) → TASK-004 (Repo Interface)
**Batch 3 (Parallel):** TASK-005 (Models), TASK-025 (Unit: Domain)
**Batch 4 (Sequential):** TASK-006 (Migration) → TASK-007 (Repo Impl) → TASK-021 (Dependencies)
**Batch 5 (Parallel):** TASK-008 through TASK-019 (all 10 commands + 2 queries)
**Batch 6:** TASK-022 (Router)
**Batch 7 (Parallel):** TASK-023 (Notifications), TASK-024 (Config), TASK-026 (Unit: App), TASK-027 (Integration Tests)
**Batch 8 (Parallel):** TASK-028 (ChangeListPage), TASK-029 (ChangeDetailPage)
**Batch 9:** TASK-030 (Frontend Config)

## Final Checklist

- [x] All 30 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] mypy passes (`make lint`)
- [x] flake8 passes (`make lint`)
- [x] TypeScript compiles (`npx tsc --noEmit` in web/app)
- [x] Server starts without errors
- [x] Migration applies cleanly
- [x] Frontend routes work
- [x] Navigation entry visible in Management section
