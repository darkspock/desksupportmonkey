# Feature 3: Retention & Integrity — Tasks

**Epic:** E29 — Audit Trail & Compliance Evidence
**Feature:** F3 — Retention & Integrity
**Design:** [design.md](design.md)

---

## TASK-001: Domain — RetentionPolicy Entity + Exception

**Layer:** Domain
**Files:** `src/audit_bc/audit/domain/entities.py`, `src/audit_bc/audit/domain/exceptions.py`

### Acceptance Criteria

- [x] Add `RetentionPolicy` dataclass to entities.py: `id, company_id, retention_months, updated_at, updated_by`
- [x] Add `create()` classmethod with default `retention_months=36`
- [x] Add `VALID_RETENTION_MONTHS = [0, 12, 24, 36, 60, 84]` constant
- [x] Add `InvalidRetentionPeriodError` to exceptions.py

---

## TASK-002: Domain — Repository Interface Extensions

**Layer:** Domain
**Files:** `src/audit_bc/audit/domain/repository.py`

### Acceptance Criteria

- [x] Add `save_retention_policy(policy: RetentionPolicy) -> None`
- [x] Add `find_retention_policy(company_id: str) -> Optional[RetentionPolicy]`
- [x] Add `find_all_retention_policies() -> list[RetentionPolicy]`
- [x] Add `delete_entries_before(company_id: str, before: datetime) -> int`
- [x] Add `find_entries_for_verification(company_id: str, date_from: datetime, date_to: datetime, page: int, page_size: int) -> list[AuditEntry]`
- [x] Import RetentionPolicy in repository.py

---

## TASK-003: Infrastructure — RetentionPolicyModel + Migration

**Layer:** Infrastructure
**Files:** `src/audit_bc/audit/infrastructure/models.py`, `alembic/versions/g7h8i9j0k1l2_create_retention_policies.py`

### Acceptance Criteria

- [x] Add `RetentionPolicyModel` with: id (ULID), company_id (FK unique), retention_months (int default 36), updated_at (DateTime tz), updated_by (FK users.id)
- [x] Create Alembic migration revising `f6g7h8i9j0k1`
- [x] Index on company_id (covered by unique constraint)

---

## TASK-004: Infrastructure — Repository Implementation

**Layer:** Infrastructure
**Files:** `src/audit_bc/audit/infrastructure/repository.py`

### Acceptance Criteria

- [x] Implement `save_retention_policy()` with upsert pattern (insert or update)
- [x] Implement `find_retention_policy()` by company_id
- [x] Implement `find_all_retention_policies()` returning all policies with retention_months > 0
- [x] Implement `delete_entries_before()` using bulk DELETE
- [x] Implement `find_entries_for_verification()` with date range and pagination, ordered by created_at ASC
- [x] Add `_to_retention_policy_entity()` converter
- [x] Import RetentionPolicyModel

---

## TASK-005: Application — Command + Query Handlers

**Layer:** Application
**Files:** `src/audit_bc/audit/application/commands/update_retention_policy.py`, `src/audit_bc/audit/application/queries/get_retention_policy.py`, `src/audit_bc/audit/application/dtos.py`

### Acceptance Criteria

- [x] Create `UpdateRetentionPolicyCommand(company_id, retention_months, updated_by)` extending Command
- [x] Create `UpdateRetentionPolicyHandler` — validates retention_months in VALID_RETENTION_MONTHS, creates/updates policy
- [x] Create `GetRetentionPolicyQuery(company_id)` extending Query
- [x] Create `GetRetentionPolicyQueryHandler` — returns RetentionPolicyDto or defaults (retention_months=36)
- [x] Add `RetentionPolicyDto(retention_months, updated_at, updated_by)` to dtos.py

---

## TASK-006: HTTP — Schemas + Endpoints

**Layer:** HTTP Adapter
**Files:** `adapters/http/api/audit/schemas.py`, `adapters/http/api/audit/routers.py`

### Acceptance Criteria

- [x] Add `UpdateRetentionRequest(retention_months: int)` schema
- [x] Add `RetentionPolicyResponse(retention_months, updated_at, updated_by)` schema
- [x] Add `VerifyIntegrityRequest(date_from?, date_to?)` schema
- [x] Add `VerifyIntegrityResponse(task_id, status?, total_checked?, valid_count?, invalid_count?, first_invalid_entry_id?)` schema
- [x] Add `GET /retention` endpoint — returns current retention policy
- [x] Add `PUT /retention` endpoint — updates retention policy, 409 on invalid period
- [x] Add `POST /verify` endpoint — dispatches verify_audit_integrity task, returns 202 with task_id
- [x] Add `GET /verify/{task_id}` endpoint — returns task status/results
- [x] All endpoints BEFORE `/{entry_id}` catch-all

---

## TASK-007: Celery Tasks — verify + purge

**Layer:** Infrastructure
**Files:** `core/tasks/audit.py`, `core/celery.py`, `core/tasks/__init__.py`

### Acceptance Criteria

- [x] Add `verify_audit_integrity` task: iterates entries chronologically, recomputes hash, compares, returns result dict
- [x] Add `retention_purge` task: iterates all retention policies, computes cutoff, creates summary audit entry, deletes expired entries
- [x] Register both tasks in `core/tasks/__init__.py`
- [x] Add `retention-purge` to Celery Beat schedule: weekly Sunday 03:00 UTC

---

## TASK-008: Unit Tests

**Layer:** Tests
**Files:** `tests/unit/audit_bc/audit/domain/test_entities.py`, `tests/unit/audit_bc/audit/application/commands/test_update_retention_policy.py`, `tests/unit/audit_bc/audit/application/queries/test_get_retention_policy.py`

### Acceptance Criteria

- [x] Test RetentionPolicy.create() with defaults and custom values
- [x] Test RetentionPolicy.create() with invalid retention_months
- [x] Test UpdateRetentionPolicyHandler: creates new policy, updates existing
- [x] Test UpdateRetentionPolicyHandler: rejects invalid retention_months
- [x] Test GetRetentionPolicyQueryHandler: returns existing policy
- [x] Test GetRetentionPolicyQueryHandler: returns defaults when no policy exists

---

## TASK-009: Integration Tests

**Layer:** Tests
**Files:** `tests/integration/test_audit_endpoints.py`

### Acceptance Criteria

- [x] Test GET /audit/retention returns defaults
- [x] Test PUT /audit/retention updates successfully
- [x] Test PUT /audit/retention rejects invalid period
- [x] Test POST /audit/verify returns 202 with task_id

---

## TASK-010: Frontend — Retention + Integrity UI

**Layer:** Frontend
**Files:** `web/app/src/pages/admin/AuditLogPage.tsx`, `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

### Acceptance Criteria

- [x] Add retention settings card: dropdown with period options, save button, warning for < 24 months
- [x] Add verify integrity button: date range picker, trigger verification, show results (polling)
- [x] Add ~15 i18n keys for both EN and ES

---

## TASK-011: Verification & Progress Tracking

**Layer:** Verification
**Files:** Multiple

### Acceptance Criteria

- [x] All unit tests pass: `python -m pytest tests/unit/ -x -q`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] mypy passes: `make lint` (ignore E501)
- [x] Mark F3 as Done in `docs/epics/e29-audit-trail/slicing.md`
- [x] Mark all tasks as done in this file
- [x] Mark E29 as Done in `docs/product/roadmap.md`
