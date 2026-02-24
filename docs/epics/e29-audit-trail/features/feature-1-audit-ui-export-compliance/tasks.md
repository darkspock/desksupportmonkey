# Implementation Tasks: Audit UI, Export & Compliance

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 18
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Entities & Exceptions | 2 | S-M |
| Domain - Repository Interface | 1 | S |
| Infrastructure - Models & Migration | 2 | M |
| Infrastructure - Repository | 1 | M |
| Application - Queries + DTOs | 1 | M |
| Application - Commands | 1 | M |
| HTTP - Plan Gating Dependency | 1 | S |
| HTTP - Audit Router | 1 | L |
| HTTP - Super Admin Endpoint | 1 | S |
| Celery - Export Task | 1 | M |
| Collateral - Wiring | 1 | S |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | L |
| Frontend - Types, Routing, Sidebar | 1 | M |
| Frontend - Pages | 1 | L |
| Frontend - i18n | 1 | M |

---

## Phase 1: Domain Layer

### TASK-001: Create ComplianceControl and AuditEntryTag Entities

**Phase:** Domain
**Complexity:** M
**Dependencies:** None

**Description:**
Add `ComplianceControl` and `AuditEntryTag` dataclasses to `src/audit_bc/audit/domain/entities.py`.

**File:** `src/audit_bc/audit/domain/entities.py`

**Implementation:**

```python
@dataclass
class ComplianceControl:
    id: str
    company_id: Optional[str]  # None = predefined/global
    code: str
    name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id: Optional[str], code: str, name: str, framework: str,
               description: Optional[str] = None, is_predefined: bool = False) -> "ComplianceControl":
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            code=code, name=name, framework=framework,
            description=description,
            is_predefined=is_predefined,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )


@dataclass
class AuditEntryTag:
    id: str
    audit_entry_id: str
    control_id: str
    tagged_by: str
    tagged_at: Optional[datetime] = None

    @classmethod
    def create(cls, audit_entry_id: str, control_id: str, tagged_by: str) -> "AuditEntryTag":
        return cls(
            id=str(ulid.new()),
            audit_entry_id=audit_entry_id,
            control_id=control_id,
            tagged_by=tagged_by,
            tagged_at=datetime.now(timezone.utc),
        )
```

**Acceptance Criteria:**
- [ ] ComplianceControl dataclass with create() classmethod
- [ ] AuditEntryTag dataclass with create() classmethod
- [ ] Both use ULID for IDs
- [ ] ComplianceControl.company_id is Optional (None for predefined)

---

### TASK-002: Create Domain Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create domain exceptions for audit compliance operations.

**File:** `src/audit_bc/audit/domain/exceptions.py` (NEW)

**Implementation:**

```python
class ControlNotFoundError(Exception): ...
class ControlCodeExistsError(Exception): ...
class PredefinedControlError(Exception): ...
class AuditEntryNotFoundError(Exception): ...
```

**Acceptance Criteria:**
- [ ] All 4 exception classes created
- [ ] Simple exception classes (no custom init needed)

---

### TASK-003: Extend Repository Interface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Add 9 abstract methods to `AuditRepositoryInterface` for tags, controls, and paginated queries.

**File:** `src/audit_bc/audit/domain/repository.py`

**Methods to add:**

```python
# Audit entry queries
@abstractmethod
def find_all(self, company_id: str, filters: dict) -> tuple[list[AuditEntry], int]: ...
@abstractmethod
def find_all_cross_company(self, filters: dict) -> tuple[list[AuditEntry], int]: ...

# Compliance controls
@abstractmethod
def save_control(self, control: ComplianceControl) -> None: ...
@abstractmethod
def find_control_by_id(self, control_id: str, company_id: Optional[str] = None) -> Optional[ComplianceControl]: ...
@abstractmethod
def find_controls(self, company_id: str) -> list[ComplianceControl]: ...
@abstractmethod
def find_control_by_code(self, code: str, company_id: Optional[str] = None) -> Optional[ComplianceControl]: ...

# Tags
@abstractmethod
def save_tag(self, tag: AuditEntryTag) -> None: ...
@abstractmethod
def delete_tag(self, tag_id: str) -> None: ...
@abstractmethod
def find_tags_by_entry(self, entry_id: str) -> list[AuditEntryTag]: ...
```

**Acceptance Criteria:**
- [ ] 9 new abstract methods added
- [ ] Imports updated for new entities
- [ ] Return types match design

---

## Phase 2: Infrastructure Layer

### TASK-004: Create Models and Migration

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Add `ComplianceControlModel` and `AuditEntryTagModel` to `src/audit_bc/audit/infrastructure/models.py`. Create Alembic migration with predefined controls seed.

**Files:**
- `src/audit_bc/audit/infrastructure/models.py` (MODIFY)
- `alembic/versions/d5e6f7g8h9i0_create_audit_tags_and_controls.py` (NEW)

**ComplianceControlModel:**
- Table: `compliance_controls`
- Columns: id (ULID), company_id (FK, nullable), code (String 50), name (String 200), framework (String 50), description (Text, nullable), is_predefined (Boolean default False), is_active (Boolean default True), created_at (DateTime TZ)
- Unique: `(company_id, code)`
- Indexes: `(company_id)`, `(framework)`

**AuditEntryTagModel:**
- Table: `audit_entry_tags`
- Columns: id (ULID), audit_entry_id (FK to audit_entries), control_id (FK to compliance_controls), tagged_by (FK to users), tagged_at (DateTime TZ)
- Unique: `(audit_entry_id, control_id)`
- Indexes: `(audit_entry_id)`, `(control_id)`

**Migration must seed ~15 predefined controls:**
- NIS2: ART21-2A, ART21-2B, ART21-2E, ART21-2I, ART21-2J
- DORA: CH2-ART5, CH2-ART9, CH3-ART17, CH3-ART19
- ISO27001: A5.1, A5.23, A6.1, A8.2, A8.15, A8.16

**Acceptance Criteria:**
- [ ] Both models use ULIDMixin + Mapped[type] annotations
- [ ] FK constraints on audit_entry_id, control_id, tagged_by
- [ ] Unique constraints on (company_id, code) and (audit_entry_id, control_id)
- [ ] Migration creates both tables
- [ ] Migration seeds 15 predefined controls (is_predefined=True, company_id=NULL)
- [ ] Migration is reversible (drop tables in downgrade)

---

### TASK-005: Implement Repository Extensions

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Implement 9 new methods in `AuditRepository`.

**File:** `src/audit_bc/audit/infrastructure/repository.py` (MODIFY)

**Key implementation details:**

- `find_all()` — Paginated query with filters: date_from, date_to, actor_id, action, resource_type, search (ilike on resource_id or actor_email), control_id (join to audit_entry_tags). Count via subquery. Order by created_at desc. Return `tuple[list[AuditEntry], int]`.
- `find_all_cross_company()` — Same as find_all but no company_id filter. Additional filter: `company_id` (optional, for super admin filtering by company).
- `save_control()` — Insert ComplianceControlModel, flush.
- `find_control_by_id()` — Select by id. If company_id provided, also match company_id OR is_predefined=True.
- `find_controls()` — Select where company_id=company_id OR company_id IS NULL (predefined). Order: is_predefined desc, framework, code.
- `find_control_by_code()` — Select by code where company_id=company_id OR company_id IS NULL.
- `save_tag()`, `delete_tag()`, `find_tags_by_entry()` — Standard CRUD.

**Add `_to_control_entity()` and `_to_tag_entity()` converter methods.**

**Acceptance Criteria:**
- [ ] All 9 methods implemented
- [ ] find_all supports all filter types from design
- [ ] find_all uses subquery count pattern for pagination
- [ ] find_controls returns predefined + company controls
- [ ] Converter methods for ComplianceControl and AuditEntryTag

---

## Phase 3: Application Layer

### TASK-006: Create Query Handlers + DTOs

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create 3 query handlers with their DTOs.

**Files:**
- `src/audit_bc/audit/application/queries/list_audit_entries.py` (NEW)
- `src/audit_bc/audit/application/queries/get_audit_entry.py` (NEW)
- `src/audit_bc/audit/application/queries/list_compliance_controls.py` (NEW)
- `src/audit_bc/audit/application/dtos.py` (NEW)

**DTOs (in dtos.py):**
- `AuditEntryDto` — list view fields + tag_count
- `AuditEntryDetailDto` — all fields + `tags: list[AuditTagDto]`
- `AuditTagDto` — id, control_id, control_code, control_name, framework, tagged_by, tagged_at
- `ComplianceControlDto` — all control fields

**ListAuditEntriesQuery:**
- Inherits from `Query`
- Fields: company_id, page, page_size, date_from, date_to, actor_id, action, resource_type, control_id, search
- Handler: Takes repo + optional `user_name_resolver` callable. Returns `tuple[list[AuditEntryDto], int]`

**GetAuditEntryQuery:**
- Fields: entry_id, company_id
- Handler: Returns `AuditEntryDetailDto`. Resolves tags by joining control info. Raises `AuditEntryNotFoundError` if not found.

**ListComplianceControlsQuery:**
- Fields: company_id
- Handler: Returns `list[ComplianceControlDto]`

**Acceptance Criteria:**
- [ ] All queries inherit from `Query`, handlers from `QueryHandler`
- [ ] DTOs are dataclasses (not Pydantic)
- [ ] ListAuditEntries supports user_name_resolver for actor names
- [ ] GetAuditEntry resolves tags with control info
- [ ] __init__.py files created for queries package

---

### TASK-007: Create Command Handlers

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create 5 command handlers for compliance controls and tags.

**Files:**
- `src/audit_bc/audit/application/commands/create_compliance_control.py` (NEW)
- `src/audit_bc/audit/application/commands/update_compliance_control.py` (NEW)
- `src/audit_bc/audit/application/commands/deactivate_compliance_control.py` (NEW)
- `src/audit_bc/audit/application/commands/add_audit_tags.py` (NEW)
- `src/audit_bc/audit/application/commands/remove_audit_tag.py` (NEW)

**CreateComplianceControlCommand:**
- Fields: company_id, code, name, framework, description
- Handler: Validates code uniqueness within company scope (check both company-specific and predefined). Creates control. Returns None.

**UpdateComplianceControlCommand:**
- Fields: control_id, company_id, name, description
- Handler: Finds control. Rejects if predefined (PredefinedControlError). Updates fields. Returns None.

**DeactivateComplianceControlCommand:**
- Fields: control_id, company_id
- Handler: Finds control. Rejects if predefined. Sets is_active=False. Returns None.

**AddAuditTagsCommand:**
- Fields: entry_id, company_id, control_ids (list), tagged_by
- Handler: Validates entry exists. Validates all controls exist. Creates AuditEntryTag for each. Skips duplicates. Returns None.

**RemoveAuditTagCommand:**
- Fields: tag_id, entry_id, company_id
- Handler: Validates entry exists (within company). Deletes tag. Returns None.

**Acceptance Criteria:**
- [ ] All commands inherit from `Command`, handlers from `CommandHandler`
- [ ] Create validates code uniqueness
- [ ] Update/Deactivate reject predefined controls
- [ ] AddAuditTags handles batch + duplicate skipping
- [ ] __init__.py files created for commands package

---

## Phase 4: HTTP Layer

### TASK-008: Create require_plan_feature Dependency

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Add `require_plan_feature()` factory function to `adapters/http/api/auth/dependencies.py`. This reusable dependency checks if the current user's company has the specified feature available on their plan.

**File:** `adapters/http/api/auth/dependencies.py` (MODIFY)

**Implementation:**

```python
def require_plan_feature(feature: str) -> Callable:
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        company = CompanyRepository(db).find_by_id(current_user.company_id)
        if not company:
            raise HTTPException(status_code=403, detail="Company not found")
        if not PlanGate.is_feature_available(
            plan=company.plan,
            billing_status=company.billing_status,
            complimentary=company.complimentary,
            open_source_mode=settings.stripe.OPEN_SOURCE_MODE,
            feature=feature,
            in_trial=company.is_in_trial(),
        ):
            raise HTTPException(status_code=402, detail=f"Feature '{feature}' requires an upgrade")
        return current_user
    return checker
```

**Acceptance Criteria:**
- [ ] Returns 402 for non-Enterprise plans when checking "audit_trail"
- [ ] Bypasses for open_source_mode, complimentary, in_trial
- [ ] Returns 403 if company not found
- [ ] Returns the current_user for downstream dependencies

---

### TASK-009: Create Audit Router, Schemas & Dependencies

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-006, TASK-007, TASK-008

**Description:**
Create the full audit HTTP module with 10 endpoints.

**Files:**
- `adapters/http/api/audit/__init__.py` (NEW)
- `adapters/http/api/audit/schemas.py` (NEW)
- `adapters/http/api/audit/dependencies.py` (NEW)
- `adapters/http/api/audit/routers.py` (NEW)

**Schemas:**
- Request: `ExportAuditRequest`, `AddAuditTagsRequest`, `CreateControlRequest`, `UpdateControlRequest`
- Response: `AuditEntryListResponse`, `AuditEntryDetailResponse`, `AuditTagResponse`, `ComplianceControlResponse`, `ExportStatusResponse`

**Dependencies:**
- `get_audit_repo(db) -> AuditRepository`
- `get_user_repo(db) -> UserRepository`

**Endpoints (all gated by `require_plan_feature("audit_trail")` + `require_role(UserRole.ADMIN)`):**

| # | Method | Route | Handler |
|---|--------|-------|---------|
| 1 | GET | `/api/v1/audit` | List audit entries (paginated) |
| 2 | GET | `/api/v1/audit/controls` | List compliance controls |
| 3 | POST | `/api/v1/audit/controls` | Create custom control |
| 4 | PUT | `/api/v1/audit/controls/{id}` | Update custom control |
| 5 | DELETE | `/api/v1/audit/controls/{id}` | Deactivate custom control |
| 6 | POST | `/api/v1/audit/export` | Request async export |
| 7 | GET | `/api/v1/audit/export/{task_id}/download` | Get download URL |
| 8 | GET | `/api/v1/audit/{id}` | Get audit entry detail |
| 9 | POST | `/api/v1/audit/{id}/tags` | Add tags to entry |
| 10 | DELETE | `/api/v1/audit/{id}/tags/{tag_id}` | Remove tag |

**Route ordering:** Static routes (`/controls`, `/export`) BEFORE parameterized `/{id}` routes to avoid catch-all conflicts.

**Export endpoint (#6):** Calls `export_audit_log.delay(...)` directly and returns `{"task_id": result.id}`.
**Download endpoint (#7):** Checks Celery task status via `AsyncResult(task_id)`. If successful, returns signed URL from S3StorageService.

**Acceptance Criteria:**
- [ ] All 10 endpoints implemented
- [ ] All endpoints use require_plan_feature("audit_trail")
- [ ] All endpoints use require_role(UserRole.ADMIN)
- [ ] Static routes before parameterized routes
- [ ] Proper error handling (404, 409, 402)
- [ ] Pagination uses PaginationMeta

---

### TASK-010: Add Super Admin Cross-Company Audit Endpoint

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
Add cross-company audit endpoint to existing super admin router.

**Files:**
- `adapters/http/api/super_admin/routers.py` (MODIFY)
- `adapters/http/api/super_admin/dependencies.py` (MODIFY — add get_audit_repo)

**Endpoint:**

```
GET /api/v1/super-admin/audit
```

Query params: page, page_size, company_id, date_from, date_to, actor_id, action, resource_type, search

Uses `require_role(UserRole.SUPER_ADMIN)`. No plan gating.

**Acceptance Criteria:**
- [ ] Endpoint uses find_all_cross_company
- [ ] Filterable by company_id
- [ ] Paginated response with PaginationMeta
- [ ] Super admin only access

---

## Phase 5: Celery Task

### TASK-011: Create Audit Export Celery Task

**Phase:** Celery
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create async audit export task following the `generate_report` pattern.

**Files:**
- `core/tasks/audit.py` (NEW)
- `templates/reports/audit_export.html` (NEW)
- `src/notification_bc/notification/domain/enums.py` (MODIFY — add AUDIT_EXPORT_READY)
- `core/tasks/__init__.py` (MODIFY — register task)

**Task:** `export_audit_log(self, company_id, requested_by, format, filters)`

**Flow:**
1. Create SessionLocal
2. Query all audit entries matching filters (no pagination — fetch all)
3. If format="csv": generate CSV with csv.writer
4. If format="pdf": render Jinja2 template → WeasyPrint PDF
5. Upload to MinIO: `audit-exports/{company_id}/{task_id}.{ext}`
6. Create notification (AUDIT_EXPORT_READY) for requested_by user
7. Commit and close session

**Acceptance Criteria:**
- [ ] Task follows generate_report pattern (bind=True, max_retries=3)
- [ ] CSV export includes all audit entry fields
- [ ] PDF export uses Jinja2 + WeasyPrint
- [ ] Upload to MinIO with S3StorageService
- [ ] Notification created on completion
- [ ] AUDIT_EXPORT_READY added to EventType enum
- [ ] Task registered in core/tasks/__init__.py

---

## Phase 6: Collateral & Wiring

### TASK-012: Register Router and Wiring

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Wire up the audit router in app.py.

**Files:**
- `app.py` (MODIFY — add audit router include)

**Implementation:**
```python
from adapters.http.api.audit.routers import router as audit_router
# ... in create_app():
application.include_router(audit_router)
```

**Acceptance Criteria:**
- [ ] Audit router imported and registered in app.py
- [ ] Router appears in API docs

---

## Phase 7: Tests

### TASK-013: Unit Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001, TASK-002, TASK-006, TASK-007

**Description:**
Create unit tests for new entities, commands, and queries.

**Files:**
- `tests/unit/audit_bc/audit/domain/test_entities.py` (MODIFY — add ComplianceControl + AuditEntryTag tests)
- `tests/unit/audit_bc/audit/domain/test_exceptions.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_create_compliance_control.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_update_compliance_control.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_deactivate_compliance_control.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_add_audit_tags.py` (NEW)
- `tests/unit/audit_bc/audit/application/commands/test_remove_audit_tag.py` (NEW)
- `tests/unit/audit_bc/audit/application/queries/test_list_audit_entries.py` (NEW)
- `tests/unit/audit_bc/audit/application/queries/test_get_audit_entry.py` (NEW)
- `tests/unit/audit_bc/audit/application/queries/test_list_compliance_controls.py` (NEW)

**Test counts:**
- Entity tests: ~6 tests (ComplianceControl.create, AuditEntryTag.create, predefined flag, defaults)
- Command handler tests: ~12 tests (success, validation failures, predefined rejection, duplicate handling)
- Query handler tests: ~6 tests (list with filters, detail with tags, empty results)

**Acceptance Criteria:**
- [ ] Entity create() tests for both new entities
- [ ] All 5 command handlers tested (success + error paths)
- [ ] All 3 query handlers tested
- [ ] Predefined control rejection tested
- [ ] Duplicate tag skipping tested

---

### TASK-014: Integration Tests

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-009, TASK-010, TASK-012

**Description:**
Create integration tests for all audit and super admin audit endpoints.

**Files:**
- `tests/integration/test_audit_endpoints.py` (NEW)

**Test coverage:**
- List audit entries (paginated, with filters)
- Get audit entry detail (with tags)
- Controls CRUD (create, update, deactivate, list)
- Predefined control protection (cannot update/delete)
- Tag management (add, remove, duplicate handling)
- Export request (returns task_id)
- Plan gating (402 for non-Enterprise)
- Role gating (403 for non-admin)
- Super admin cross-company endpoint

**Acceptance Criteria:**
- [ ] All 10 audit endpoints tested
- [ ] Super admin endpoint tested
- [ ] Plan gating returns 402
- [ ] Role gating returns 403
- [ ] Predefined controls cannot be modified/deleted
- [ ] Duplicate tags handled gracefully

---

## Phase 8: Frontend

### TASK-015: Frontend Types, Routing & Sidebar

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-009

**Description:**
Add TypeScript interfaces, routes, and sidebar navigation.

**Files:**
- `web/app/src/types/index.ts` (MODIFY)
- `web/app/src/router.tsx` (MODIFY)
- `web/app/src/components/layout/Sidebar.tsx` (MODIFY)

**Types to add:**
- `AuditEntry` — list view fields
- `AuditEntryDetail` — all fields + tags
- `AuditTag` — tag with control info
- `ComplianceControl` — control fields
- `AuditExportStatus` — task_id, status, download_url

**Routes:**
- `/audit` → AuditLogPage (admin)
- `/audit/:id` → AuditEntryDetailPage (admin)
- `/settings/compliance` → ComplianceControlsPage (admin)
- `/super-admin/audit` → CrossCompanyAuditPage (super admin)

**Sidebar:**
- "Audit Log" under Security section (admin, Enterprise only)
- "Compliance" under Management > Configuration (admin, Enterprise only)
- "Audit" in super admin section

**Acceptance Criteria:**
- [ ] All TypeScript interfaces added
- [ ] All routes registered
- [ ] Sidebar items show for correct roles
- [ ] Enterprise feature gating in sidebar (hide for non-Enterprise)

---

### TASK-016: Frontend Pages

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-015

**Description:**
Create the 4 audit-related pages.

**Files:**
- `web/app/src/pages/admin/AuditLogPage.tsx` (NEW)
- `web/app/src/pages/admin/AuditEntryDetailPage.tsx` (NEW)
- `web/app/src/pages/admin/ComplianceControlsPage.tsx` (NEW)
- `web/app/src/pages/superadmin/CrossCompanyAuditPage.tsx` (NEW)

**AuditLogPage:**
- Paginated table: timestamp, actor (name + email), action, resource type, resource ID, IP, tag count
- Filters: date range picker, actor dropdown, action type, resource type, compliance tag
- Search box (resource ID or actor)
- Export button → modal (format selection) → triggers export → notification on completion
- Row click → navigate to detail

**AuditEntryDetailPage:**
- Full metadata grid: all audit entry fields
- Before/after JSON diff viewer (for entries with `changes`)
- Compliance tags section: list of tags with remove button, add tag dropdown
- Back button to list

**ComplianceControlsPage:**
- Table: code, name, framework, predefined badge, active status, actions
- Create button → modal (code, name, framework, description)
- Edit button (custom only) → modal
- Deactivate button (custom only) → confirmation
- Predefined controls: lock icon, no edit/delete

**CrossCompanyAuditPage:**
- Same as AuditLogPage but with company name column and company filter
- No tag management (view only)

**Acceptance Criteria:**
- [ ] All 4 pages created
- [ ] Pagination works
- [ ] Filters work
- [ ] Export triggers Celery task
- [ ] Tag add/remove works
- [ ] Controls CRUD works
- [ ] Predefined controls protected in UI
- [ ] Company filter in super admin view

---

### TASK-017: Frontend i18n

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-016

**Description:**
Add ~50 i18n keys for EN and ES.

**Files:**
- `web/app/src/locales/en.ts` (MODIFY)
- `web/app/src/locales/es.ts` (MODIFY)

**Key groups:**
- `audit.log.*` — Audit log page labels, filters, table headers
- `audit.detail.*` — Detail page labels, sections
- `audit.export.*` — Export dialog, status messages
- `audit.tags.*` — Tag management labels
- `audit.controls.*` — Compliance controls page labels
- `audit.superAdmin.*` — Super admin audit page labels

**Acceptance Criteria:**
- [ ] ~50 keys added to both EN and ES
- [ ] All UI text uses i18n keys (no hardcoded strings)
- [ ] Spanish translations are natural (not machine-translated)

---

## Phase 9: Completion

### TASK-018: Final Verification & Progress Tracking

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Run all tests, lint checks, and update progress tracking documents.

**Verification steps:**
1. `python -m pytest tests/unit/ -x -q` — all pass
2. `make test-integration` — all pass
3. `make lint` — 0 errors
4. Frontend: `npx tsc --noEmit` — compiles clean

**Progress tracking updates:**
- Mark F1 as "Done" in `docs/epics/e29-audit-trail/slicing.md`

**Acceptance Criteria:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] mypy + flake8 clean
- [ ] Frontend compiles
- [ ] F1 marked Done in slicing.md

---

## Dependency Graph

```
TASK-001 (Entities)    TASK-002 (Exceptions)   TASK-008 (Plan Gate)
    │                      │                        │
    ├──────────────────────┤                        │
    │                      │                        │
TASK-003 (Repo Interface)  │                        │
    │                      │                        │
TASK-004 (Models + Migration)                       │
    │                                               │
TASK-005 (Repo Implementation)                      │
    │                                               │
    ├──────────────────────┐                        │
    │                      │                        │
TASK-006 (Queries)    TASK-007 (Commands)           │
    │                      │                        │
    ├──────────────────────┤────────────────────────┤
    │                      │
TASK-009 (Audit Router)   TASK-010 (Super Admin)  TASK-011 (Celery Task)
    │                      │                        │
TASK-012 (Wiring)          │                        │
    │                      │                        │
    ├──────────────────────┤────────────────────────┤
    │
TASK-013 (Unit Tests)  TASK-014 (Integration Tests)
    │
TASK-015 (FE Types/Routing)
    │
TASK-016 (FE Pages)
    │
TASK-017 (FE i18n)
    │
TASK-018 (Verification)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002, TASK-008
**Batch 2:** TASK-003
**Batch 3:** TASK-004
**Batch 4:** TASK-005
**Batch 5 (Parallel):** TASK-006, TASK-007, TASK-011
**Batch 6 (Parallel):** TASK-009, TASK-010
**Batch 7:** TASK-012
**Batch 8 (Parallel):** TASK-013, TASK-014
**Batch 9:** TASK-015
**Batch 10:** TASK-016
**Batch 11:** TASK-017
**Batch 12:** TASK-018

## Final Checklist

- [ ] All 18 tasks completed
- [ ] All tests passing (unit + integration)
- [ ] mypy + flake8 clean
- [ ] Frontend compiles
- [ ] F1 marked Done in slicing.md
- [ ] All acceptance criteria from requirements.md verified
