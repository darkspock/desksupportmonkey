# Implementation Tasks: GDPR Operations

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 14
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums, Entity & Exceptions | 2 | S-M |
| Domain - Repository Interface | 1 | S |
| Infrastructure - Models & Migrations | 1 | M |
| Infrastructure - Repository | 1 | M |
| Application - Commands + Queries + DTOs | 2 | M |
| HTTP - Endpoints & Schemas | 1 | M |
| Celery - GDPR Tasks | 1 | L |
| Collateral - User Entity + Wiring | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Frontend | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create Enums

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create `src/audit_bc/audit/domain/enums.py` with GDPR-related enums.

**File:** `src/audit_bc/audit/domain/enums.py` (NEW)

**Implementation:**

```python
from enum import Enum

class GdprRequestType(str, Enum):
    EXPORT = "export"
    ANONYMIZE = "anonymize"

class GdprRequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**Acceptance Criteria:**
- [x] Both enums created as str+Enum
- [x] Values are lowercase strings

---

### TASK-002: Create GdprRequest Entity and Exceptions

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Add `GdprRequest` dataclass to `src/audit_bc/audit/domain/entities.py` with state machine methods. Add 5 GDPR exceptions to `exceptions.py`.

**File:** `src/audit_bc/audit/domain/entities.py` (MODIFY)

**GdprRequest fields:**
- id, company_id, target_user_id, target_user_email, requested_by
- request_type (GdprRequestType), status (GdprRequestStatus)
- reason (Optional), storage_key (Optional), error_message (Optional)
- started_at (Optional), completed_at (Optional), created_at (Optional)

**State machine methods:**
- `create()` classmethod — sets status=PENDING
- `start_processing()` — PENDING → PROCESSING, sets started_at
- `complete(storage_key=None)` — PROCESSING → COMPLETED, sets completed_at
- `fail(error_message)` — PROCESSING → FAILED, sets completed_at, error_message
- `cancel()` — PENDING → CANCELLED

Each transition validates current status, raises `InvalidGdprStatusTransitionError` on invalid.

**File:** `src/audit_bc/audit/domain/exceptions.py` (MODIFY)

Add:
- `GdprRequestNotFoundError`
- `InvalidGdprStatusTransitionError`
- `CannotAnonymizeSuperAdminError`
- `CannotAnonymizeSelfError`
- `UserAlreadyAnonymizedError`
- `TargetUserNotFoundError`

**Acceptance Criteria:**
- [x] GdprRequest dataclass with ULID ID generation
- [x] State machine transitions validated
- [x] Invalid transitions raise InvalidGdprStatusTransitionError
- [x] All 6 exception classes created

---

### TASK-003: Extend Repository Interface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add 4 abstract methods to `AuditRepositoryInterface` for GDPR requests.

**File:** `src/audit_bc/audit/domain/repository.py` (MODIFY)

**Methods:**
```python
@abstractmethod
def save_gdpr_request(self, request: GdprRequest) -> None: ...
@abstractmethod
def find_gdpr_request_by_id(self, request_id: str, company_id: Optional[str] = None) -> Optional[GdprRequest]: ...
@abstractmethod
def find_gdpr_requests(self, company_id: str, filters: dict) -> tuple[list[GdprRequest], int]: ...
@abstractmethod
def anonymize_actor_email(self, actor_id: str, anonymized_email: str) -> int: ...
```

**Acceptance Criteria:**
- [x] 4 new abstract methods added
- [x] Imports updated for GdprRequest

---

## Phase 2: Infrastructure Layer

### TASK-004: Create Model and Migrations

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002

**Description:**
Add `GdprRequestModel` to models.py. Create 2 migrations: gdpr_requests table + user is_anonymized column.

**Files:**
- `src/audit_bc/audit/infrastructure/models.py` (MODIFY)
- `alembic/versions/e5f6g7h8i9j0_create_gdpr_requests.py` (NEW)
- `alembic/versions/f6g7h8i9j0k1_add_user_is_anonymized.py` (NEW)

**GdprRequestModel:**
- Table: `gdpr_requests`
- Uses ULIDMixin (no TimestampMixin — has custom created_at)
- Columns per design: company_id (FK), target_user_id (FK), target_user_email, requested_by (FK), request_type, status, reason, storage_key, error_message, started_at, completed_at, created_at
- Indexes: (company_id), (company_id, status), (target_user_id)

**Migration 1:** e5f6g7h8i9j0 (revises d5e6f7g8h9i0)
- Create gdpr_requests table with indexes

**Migration 2:** f6g7h8i9j0k1 (revises e5f6g7h8i9j0)
- Add `is_anonymized` Boolean column to users (default False)

**Acceptance Criteria:**
- [x] GdprRequestModel uses ULIDMixin + Mapped[type]
- [x] FK constraints on company_id, target_user_id, requested_by
- [x] Proper indexes
- [x] Both migrations reversible

---

### TASK-005: Implement Repository Methods

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Implement 4 GDPR methods in `AuditRepository`.

**File:** `src/audit_bc/audit/infrastructure/repository.py` (MODIFY)

**Key implementations:**
- `save_gdpr_request()` — insert or update (check existing by id)
- `find_gdpr_request_by_id()` — select by id, optionally filter by company_id
- `find_gdpr_requests()` — paginated with filters: status, request_type, search (target_user_email ilike). Order by created_at desc.
- `anonymize_actor_email(actor_id, anonymized_email)` — bulk UPDATE audit_entries SET actor_email = :email WHERE actor_id = :actor_id. Returns row count.

Add `_to_gdpr_request_entity()` converter.

**Acceptance Criteria:**
- [x] All 4 methods implemented
- [x] anonymize_actor_email uses bulk SQL update
- [x] find_gdpr_requests supports pagination + filters
- [x] Converter method for GdprRequest

---

## Phase 3: Application Layer

### TASK-006: Create Command Handlers

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create 3 command handlers for GDPR operations.

**Files:**
- `src/audit_bc/audit/application/commands/request_gdpr_export.py` (NEW)
- `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` (NEW)
- `src/audit_bc/audit/application/commands/cancel_gdpr_request.py` (NEW)

**RequestGdprExportCommand:**
- Fields: company_id, target_user_email, requested_by
- Handler: Takes audit_repo + user_repo. Find user by email in company. Raise TargetUserNotFoundError if not found. Create GdprRequest(type=EXPORT). Save. Return request_id.
- Does NOT dispatch Celery task — the router does that after commit.

**RequestGdprAnonymizeCommand:**
- Fields: company_id, target_user_email, requested_by, reason
- Handler: Find user by email. Validate:
  - Not super_admin → CannotAnonymizeSuperAdminError
  - Not self (requested_by != target.id) → CannotAnonymizeSelfError
  - Not already anonymized (user.is_anonymized) → UserAlreadyAnonymizedError
- Create GdprRequest(type=ANONYMIZE). Save. Return request_id.

**CancelGdprRequestCommand:**
- Fields: request_id, company_id
- Handler: Find request. Call `cancel()`. Save.

**Acceptance Criteria:**
- [x] All commands inherit from Command, handlers from CommandHandler
- [x] Export validates target user exists
- [x] Anonymize validates super_admin, self, already anonymized
- [x] Cancel calls state machine method
- [x] __init__.py files created

---

### TASK-007: Create Query Handlers + DTO

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create 2 query handlers and GdprRequestDto.

**Files:**
- `src/audit_bc/audit/application/queries/list_gdpr_requests.py` (NEW)
- `src/audit_bc/audit/application/queries/get_gdpr_request.py` (NEW)
- `src/audit_bc/audit/application/dtos.py` (MODIFY — add GdprRequestDto)

**GdprRequestDto:**
- All GdprRequest fields as dataclass

**ListGdprRequestsQuery:**
- Fields: company_id, page, page_size, status, request_type, search
- Handler: Returns `tuple[list[GdprRequestDto], int]`

**GetGdprRequestQuery:**
- Fields: request_id, company_id
- Handler: Returns `GdprRequestDto`. Raises GdprRequestNotFoundError.

**Acceptance Criteria:**
- [x] Queries inherit from Query, handlers from QueryHandler
- [x] DTO is a dataclass
- [x] List supports pagination + filters

---

## Phase 4: HTTP Layer

### TASK-008: Add GDPR Endpoints and Schemas

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-006, TASK-007

**Description:**
Add 5 GDPR endpoints to the existing audit router. Add request/response schemas.

**Files:**
- `adapters/http/api/audit/schemas.py` (MODIFY)
- `adapters/http/api/audit/routers.py` (MODIFY)

**Schemas:**
- `GdprExportRequest(target_user_email: str)`
- `GdprAnonymizeRequest(target_user_email: str, reason: str)`
- `GdprRequestListResponse(id, target_user_email, request_type, status, reason, started_at, completed_at, created_at)`
- `GdprRequestDetailResponse` — extends with download_url (Optional)

**Endpoints (all gated by require_plan_feature("audit_trail") + require_role(ADMIN)):**

| # | Method | Route | Description |
|---|--------|-------|-------------|
| 1 | GET | `/api/v1/audit/gdpr` | List GDPR requests |
| 2 | POST | `/api/v1/audit/gdpr/export` | Request data export |
| 3 | POST | `/api/v1/audit/gdpr/anonymize` | Request anonymization |
| 4 | GET | `/api/v1/audit/gdpr/{id}` | Get request detail |
| 5 | POST | `/api/v1/audit/gdpr/{id}/cancel` | Cancel pending request |

**Route placement:** Add GDPR routes BEFORE existing `/{entry_id}` catch-all in audit router. Static routes before parameterized.

**Export endpoint:** After command returns request_id, dispatch `gdpr_data_export.delay(request_id)` and return 202 with request_id.
**Anonymize endpoint:** After command returns request_id, dispatch `gdpr_anonymize_user.delay(request_id)` and return 202 with request_id.
**Detail endpoint:** If export completed, generate signed URL from storage_key.

**Acceptance Criteria:**
- [x] All 5 endpoints implemented
- [x] Plan gating + admin role
- [x] Export/anonymize return 202
- [x] Celery tasks dispatched from router after command
- [x] Detail includes download_url for completed exports
- [x] Static routes before parameterized

---

## Phase 5: Celery Tasks

### TASK-009: Create GDPR Celery Tasks

**Phase:** Celery
**Complexity:** L
**Dependencies:** TASK-005

**Description:**
Create async GDPR tasks following the audit export pattern.

**Files:**
- `core/tasks/gdpr.py` (NEW)
- `core/tasks/__init__.py` (MODIFY — register tasks)
- `src/notification_bc/notification/domain/enums.py` (MODIFY — add 2 event types)

**gdpr_data_export(self, gdpr_request_id):**
1. Load GdprRequest, start_processing(), flush
2. Load target user
3. Collect data (all queries in same session):
   - User profile → JSON
   - Assets (SELECT from asset_items WHERE assigned_to = user_id)
   - Requests (SELECT from service_requests WHERE created_by = user_id)
   - Comments (SELECT from comments WHERE author_id = user_id)
   - Notifications (SELECT from notifications WHERE user_id = user_id)
   - Audit entries (SELECT from audit_entries WHERE actor_id = user_id)
4. Generate ZIP using `zipfile` module with JSON files
5. Upload to MinIO: `gdpr-exports/{company_id}/{request_id}.zip`
6. complete(storage_key), save
7. Create GDPR_DATA_EXPORT_READY notification
8. Commit

**gdpr_anonymize_user(self, gdpr_request_id):**
1. Load GdprRequest, start_processing(), flush
2. Load target user via UserRepository
3. Generate anonymized_email: `anonymized-{sha256(user.id)[:6]}@redacted.local`
4. Update user: email, name, password_hash=None, google_id=None, microsoft_id=None, is_anonymized=True, is_active=False
5. Save user via UserRepository
6. Bulk update audit entries: `anonymize_actor_email(user.id, anonymized_email)`
7. complete(), save
8. Create GDPR_ANONYMIZATION_COMPLETED notification
9. Commit

**Event types to add:**
- `GDPR_DATA_EXPORT_READY = "gdpr.data_export_ready"`
- `GDPR_ANONYMIZATION_COMPLETED = "gdpr.anonymization_completed"`

**Acceptance Criteria:**
- [x] Both tasks use bind=True, max_retries=3 pattern
- [x] Export generates ZIP with all user data
- [x] Anonymize updates user + bulk updates audit entries
- [x] Notifications created on completion
- [x] Event types added to EventType enum
- [x] Tasks registered in core/tasks/__init__.py

---

## Phase 6: Collateral Changes

### TASK-010: Modify User Entity + Wiring

**Phase:** Collateral
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Add `is_anonymized` field to User entity, model, and repository.

**Files:**
- `src/auth_bc/user/domain/entities.py` (MODIFY)
- `src/auth_bc/user/infrastructure/models.py` (MODIFY)
- `src/auth_bc/user/infrastructure/repository.py` (MODIFY)

**User entity:** Add `is_anonymized: bool = False` field.
**UserModel:** Add `is_anonymized: Mapped[bool] = mapped_column(Boolean, default=False)`.
**UserRepository:**
- `save()` — include is_anonymized in both create and update paths
- `_to_entity()` — include is_anonymized in entity construction

**Acceptance Criteria:**
- [x] User entity has is_anonymized field with default False
- [x] UserModel has is_anonymized column
- [x] Repository save + convert updated

---

## Phase 7: Tests

### TASK-011: Unit Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-002, TASK-006, TASK-007

**Description:**
Create unit tests for GDPR entity, commands, and queries.

**Files:**
- `tests/unit/audit_bc/audit/domain/test_entities.py` (MODIFY — add GdprRequest tests)
- `tests/unit/audit_bc/audit/application/commands/test_request_gdpr_export.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_request_gdpr_anonymize.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_cancel_gdpr_request.py` (NEW)
- `tests/unit/audit_bc/audit/application/queries/test_list_gdpr_requests.py` (NEW)
- `tests/unit/audit_bc/audit/application/queries/test_get_gdpr_request.py` (NEW)
- `tests/unit/notification_bc/notification/domain/test_entities.py` (MODIFY — update EventType count)

**Test coverage:**
- GdprRequest.create() defaults
- State transitions: happy path + invalid transitions
- Export command: success + user not found
- Anonymize command: success + super_admin rejection + self rejection + already anonymized
- Cancel command: success + not pending rejection
- Query handlers: list paginated, detail found, detail not found

**Acceptance Criteria:**
- [x] Entity state machine fully tested
- [x] All 3 command handlers tested (success + error paths)
- [x] Both query handlers tested
- [x] EventType count updated

---

### TASK-012: Integration Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Create integration tests for GDPR endpoints.

**File:** `tests/integration/test_audit_endpoints.py` (MODIFY — add GDPR test class)

**Test coverage:**
- List GDPR requests (empty, with data)
- Request export (success, user not found)
- Request anonymization (success, super_admin rejection, self rejection)
- Cancel pending request (success, not pending)
- Detail with download URL
- Plan gating (402)
- Role gating (403 for non-admin)

**Acceptance Criteria:**
- [x] All 5 GDPR endpoints tested
- [x] Validation rejections tested
- [x] Plan/role gating tested

---

## Phase 8: Frontend

### TASK-013: Frontend — Types, Route, Sidebar, Page, i18n

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Add GdprRequest TypeScript interface, route, sidebar item, page, and i18n keys.

**Files:**
- `web/app/src/types/index.ts` (MODIFY)
- `web/app/src/router.tsx` (MODIFY)
- `web/app/src/components/layout/Sidebar.tsx` (MODIFY)
- `web/app/src/pages/admin/GdprRequestsPage.tsx` (NEW)
- `web/app/src/locales/en.ts` (MODIFY)
- `web/app/src/locales/es.ts` (MODIFY)

**TypeScript interface:**
```typescript
interface GdprRequest {
  id: string;
  target_user_email: string;
  request_type: string;
  status: string;
  reason: string | null;
  error_message: string | null;
  download_url: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}
```

**Route:** `/settings/gdpr` → GdprRequestsPage (admin)
**Sidebar:** "GDPR Requests" under Management > Configuration (admin)
**Icon:** Shield/lock icon

**Page features:**
- Paginated table: target email, type badge, status badge, dates, actions
- "Export Data" button → modal (enter user email) → POST
- "Anonymize Data" button → modal (enter user email + reason) → POST
- Cancel button for pending requests
- Download link for completed exports
- Status auto-refresh (refetchInterval for pending/processing)

**i18n:** ~20 keys per locale

**Acceptance Criteria:**
- [x] TypeScript interface added
- [x] Route registered
- [x] Sidebar item visible for admin
- [x] Page with CRUD + export/anonymize modals
- [x] i18n keys in EN and ES
- [x] TypeScript compiles clean

---

## Phase 9: Verification

### TASK-014: Final Verification & Progress Tracking

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Verification steps:**
1. `python -m pytest tests/unit/ -x -q` — all pass
2. `make lint` — 0 new errors (ignoring pre-existing E501)
3. Frontend: `npx tsc --noEmit` — compiles clean

**Progress tracking:**
- Mark F2 as "Done" in `docs/epics/e29-audit-trail/slicing.md`

**Acceptance Criteria:**
- [x] All unit tests pass
- [x] mypy + flake8 clean (no new errors)
- [x] Frontend compiles
- [x] F2 marked Done in slicing.md

---

## Dependency Graph

```
TASK-001 (Enums)
    │
TASK-002 (Entity + Exceptions)
    │
TASK-003 (Repo Interface)    TASK-004 (Models + Migrations)    TASK-010 (User Entity)
    │                              │
TASK-005 (Repo Implementation)     │
    │                              │
    ├──────────────────────────────┤
    │                              │
TASK-006 (Commands)    TASK-007 (Queries)    TASK-009 (Celery Tasks)
    │                      │
TASK-008 (HTTP Endpoints)  │
    │                      │
    ├──────────────────────┤
    │
TASK-011 (Unit Tests)    TASK-012 (Integration Tests)
    │
TASK-013 (Frontend)
    │
TASK-014 (Verification)
```

## Execution Order

**Batch 1:** TASK-001
**Batch 2 (Parallel):** TASK-002, TASK-010
**Batch 3:** TASK-003
**Batch 4:** TASK-004
**Batch 5 (Parallel):** TASK-005, TASK-009
**Batch 6 (Parallel):** TASK-006, TASK-007
**Batch 7:** TASK-008
**Batch 8 (Parallel):** TASK-011, TASK-012
**Batch 9:** TASK-013
**Batch 10:** TASK-014
