# Solution Design: Audit UI, Export & Compliance

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Bounded Context:** `audit_bc`

## Summary

F1 adds the admin-facing audit trail UI and compliance tagging system. It introduces two new entities (`ComplianceControl`, `AuditEntryTag`), extends the audit repository with paginated queries and filter support, adds a Celery export task (CSV/PDF to MinIO), and creates a new `adapters/http/api/audit/` router module with plan gating. A `require_plan_feature` reusable dependency is introduced for Enterprise feature gating at the HTTP layer.

## Architecture Decisions

1. **`require_plan_feature` dependency** — Created as a reusable FastAPI dependency factory in `adapters/http/api/auth/dependencies.py` (alongside `require_role`). This pattern loads the company from DB, checks `PlanGate.is_feature_available()`, and raises 402 if denied. Reusable for future Enterprise features (SLA, knowledge base, etc.).

2. **ComplianceControl as a separate entity** (not embedded in AuditEntry) — Controls are a managed catalog with their own lifecycle. Tagging is a many-to-many relationship via `AuditEntryTag` join table.

3. **AuditEntryTag preserves AuditEntry immutability** — Tags are stored in a separate join table. The `AuditEntry` entity itself is never modified after creation (important for integrity).

4. **Async export via Celery** — Follows the existing `generate_report` pattern. Export runs in background, uploads to MinIO, creates notification with signed download URL. This avoids timeouts on large audit logs.

5. **Predefined controls seeded via migration** — Not via seed script, so they exist in all environments (dev, staging, prod). Custom controls are per-company.

6. **Queries use framework base classes** — `ListAuditEntriesQuery(Query)` + `ListAuditEntriesQueryHandler(QueryHandler)`. Commands also use `Command`/`CommandHandler` from `src/framework/`.

7. **Super admin cross-company endpoint** — Added to existing `adapters/http/api/super_admin/routers.py` (not in audit router). No plan gating for super admin.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| AuditEntry entity | `src/audit_bc/audit/domain/entities.py` | Yes | No changes |
| AuditEntryModel | `src/audit_bc/audit/infrastructure/models.py` | Yes | No changes |
| AuditRepository | `src/audit_bc/audit/infrastructure/repository.py` | Yes | Add 9 methods for tags, controls, paginated queries |
| AuditRepositoryInterface | `src/audit_bc/audit/domain/repository.py` | Yes | Add 9 abstract methods |
| PlanGate | `src/company_bc/company/domain/plan_gate.py` | Yes | No changes |
| require_role | `adapters/http/api/auth/dependencies.py` | Yes | No changes |
| S3StorageService | `core/storage.py` | Yes | No changes |
| generate_report task | `core/tasks/reports.py` | Pattern reference | New task follows same pattern |
| EventType enum | `src/notification_bc/notification/domain/enums.py` | Yes | Add `AUDIT_EXPORT_READY` |
| PaginationMeta | `adapters/http/schemas/responses.py` | Yes | No changes |
| super_admin router | `adapters/http/api/super_admin/routers.py` | Yes | Add cross-company audit endpoint |
| app.py | `app.py` | Yes | Add audit router include |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| ComplianceControl | `src/audit_bc/audit/domain/entities.py` | Predefined + custom compliance framework controls |
| AuditEntryTag | `src/audit_bc/audit/domain/entities.py` | Join entity linking audit entries to controls |

**ComplianceControl dataclass:**
```python
@dataclass
class ComplianceControl:
    id: str
    company_id: Optional[str]  # None = predefined/global
    code: str                  # e.g. "NIS2-ART21-2A"
    name: str                  # e.g. "Risk analysis policies"
    framework: str             # e.g. "NIS2", "DORA", "ISO27001"
    description: Optional[str]
    is_predefined: bool        # True = seeded, read-only
    is_active: bool            # Soft delete for custom controls
    created_at: Optional[datetime]
```

**AuditEntryTag dataclass:**
```python
@dataclass
class AuditEntryTag:
    id: str
    audit_entry_id: str
    control_id: str
    tagged_by: str      # user ID who added the tag
    tagged_at: Optional[datetime]
```

#### Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| ControlNotFoundError | `src/audit_bc/audit/domain/exceptions.py` (NEW) | Control not found |
| ControlCodeExistsError | `src/audit_bc/audit/domain/exceptions.py` | Duplicate code within company scope |
| PredefinedControlError | `src/audit_bc/audit/domain/exceptions.py` | Cannot modify/delete predefined controls |
| AuditEntryNotFoundError | `src/audit_bc/audit/domain/exceptions.py` | Audit entry not found |

#### Repository Interface Extensions

Add to `AuditRepositoryInterface`:

```python
# Audit entry queries
def find_all(self, company_id: str, filters: dict) -> tuple[list[AuditEntry], int]
def find_all_cross_company(self, filters: dict) -> tuple[list[AuditEntry], int]

# Compliance controls
def save_control(self, control: ComplianceControl) -> None
def find_control_by_id(self, control_id: str, company_id: Optional[str] = None) -> Optional[ComplianceControl]
def find_controls(self, company_id: str) -> list[ComplianceControl]
def find_control_by_code(self, code: str, company_id: Optional[str] = None) -> Optional[ComplianceControl]

# Tags
def save_tag(self, tag: AuditEntryTag) -> None
def delete_tag(self, tag_id: str) -> None
def find_tags_by_entry(self, entry_id: str) -> list[AuditEntryTag]
```

### 2. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| `CreateComplianceControlCommand` | `CreateComplianceControlHandler` | Create custom control (validates unique code within company scope) |
| `UpdateComplianceControlCommand` | `UpdateComplianceControlHandler` | Update custom control (rejects predefined) |
| `DeactivateComplianceControlCommand` | `DeactivateComplianceControlHandler` | Soft delete custom control (rejects predefined) |
| `AddAuditTagsCommand` | `AddAuditTagsHandler` | Add one or more compliance tags to an audit entry |
| `RemoveAuditTagCommand` | `RemoveAuditTagHandler` | Remove a tag from an audit entry |
| `RequestAuditExportCommand` | `RequestAuditExportHandler` | Enqueue Celery export task, return task ID |

All commands inherit from `Command` and handlers from `CommandHandler`. Per CQRS, handlers return `None`.

**Exception:** `RequestAuditExportHandler` needs to return the Celery task ID. Following the existing `generate_report` pattern, the command handler doesn't return — instead, it creates a report-like tracking record. However, since we don't have a separate "AuditExport" entity, the handler will directly call `celery_task.delay()`. The Celery task ID is returned from the router by calling the task directly (same pattern as `generate_report` in the reports router where the endpoint calls `generate_report.delay(report.id)` after creating the report).

**Revised approach:** The `RequestAuditExportCommand` handler will not exist as a formal command. Instead, the router endpoint will directly enqueue the Celery task (matching the reports pattern). This keeps it simple.

#### Queries

| Query | Handler | Return Type | Description |
|-------|---------|-------------|-------------|
| `ListAuditEntriesQuery` | `ListAuditEntriesQueryHandler` | `tuple[list[AuditEntryDto], int]` | Paginated, filtered list |
| `GetAuditEntryQuery` | `GetAuditEntryQueryHandler` | `AuditEntryDetailDto` | Entry detail with tags |
| `ListComplianceControlsQuery` | `ListComplianceControlsQueryHandler` | `list[ComplianceControlDto]` | All controls (predefined + custom) |

**ListAuditEntriesQuery filters:**
- `company_id: str`
- `page: int`, `page_size: int`
- `date_from: Optional[datetime]`, `date_to: Optional[datetime]`
- `actor_id: Optional[str]`
- `action: Optional[str]`
- `resource_type: Optional[str]`
- `control_id: Optional[str]` (filter by compliance tag)
- `search: Optional[str]` (resource_id or actor_email)

**DTOs (dataclasses, not Pydantic):**

```python
@dataclass
class AuditEntryDto:
    id: str
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    response_status: int
    ip_address: Optional[str]
    created_at: Optional[datetime]
    tag_count: int

@dataclass
class AuditEntryDetailDto:
    # All AuditEntry fields + resolved tags
    id: str
    company_id: Optional[str]
    actor_id: Optional[str]
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    http_path: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[dict]
    response_status: int
    changes: Optional[dict]
    hash: str
    created_at: Optional[datetime]
    tags: list[AuditTagDto]

@dataclass
class AuditTagDto:
    id: str
    control_id: str
    control_code: str
    control_name: str
    framework: str
    tagged_by: str
    tagged_at: Optional[datetime]

@dataclass
class ComplianceControlDto:
    id: str
    code: str
    name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime]
```

### 3. Infrastructure Layer

#### Models

| Model | Table | Description |
|-------|-------|-------------|
| `ComplianceControlModel` | `compliance_controls` | Predefined + custom controls |
| `AuditEntryTagModel` | `audit_entry_tags` | Join table for entry-control links |

**ComplianceControlModel:**
```python
class ComplianceControlModel(ULIDMixin, Base):
    __tablename__ = "compliance_controls"

    company_id: Mapped[Optional[str]]  # NULL = predefined
    code: Mapped[str]                  # String(50)
    name: Mapped[str]                  # String(200)
    framework: Mapped[str]             # String(50)
    description: Mapped[Optional[str]] # Text
    is_predefined: Mapped[bool]        # default False
    is_active: Mapped[bool]            # default True
    created_at: Mapped[datetime]

    # Unique constraint: (company_id, code) — allows same code across companies
    # Predefined controls have company_id=NULL
```

**AuditEntryTagModel:**
```python
class AuditEntryTagModel(ULIDMixin, Base):
    __tablename__ = "audit_entry_tags"

    audit_entry_id: Mapped[str]   # FK to audit_entries.id
    control_id: Mapped[str]       # FK to compliance_controls.id
    tagged_by: Mapped[str]        # FK to users.id
    tagged_at: Mapped[datetime]

    # Unique constraint: (audit_entry_id, control_id) — no duplicate tags
    # Indexes: (audit_entry_id), (control_id)
```

#### Repository Extensions

Implement 9 new methods in `AuditRepository`:

- `find_all()` — Paginated query with filters. Uses subquery count pattern (like risk `find_all`). Joins `audit_entry_tags` when filtering by `control_id`. Adds `tag_count` subquery for list view.
- `find_all_cross_company()` — Same as `find_all` but without `company_id` filter. Adds `company_name` resolution via join to `companies` table.
- `save_control()`, `find_control_by_id()`, `find_controls()`, `find_control_by_code()` — Standard CRUD for compliance controls.
- `save_tag()`, `delete_tag()`, `find_tags_by_entry()` — Tag operations.

#### Migration

**`alembic/versions/xxxx_create_audit_tags_and_controls.py`:**
1. Create `compliance_controls` table
2. Create `audit_entry_tags` table with FKs
3. Seed predefined compliance controls (NIS2, DORA, ISO 27001)

**Predefined controls catalog (~15 controls):**

| Framework | Code | Name |
|-----------|------|------|
| NIS2 | NIS2-ART21-2A | Risk analysis and information security policies |
| NIS2 | NIS2-ART21-2B | Incident handling |
| NIS2 | NIS2-ART21-2E | Security in network and information systems |
| NIS2 | NIS2-ART21-2I | Human resources security and access control |
| NIS2 | NIS2-ART21-2J | Multi-factor authentication |
| DORA | DORA-CH2-ART5 | ICT risk management framework |
| DORA | DORA-CH2-ART9 | Protection and prevention |
| DORA | DORA-CH3-ART17 | ICT-related incident management process |
| DORA | DORA-CH3-ART19 | Reporting of major ICT incidents |
| ISO27001 | ISO27001-A5.1 | Policies for information security |
| ISO27001 | ISO27001-A5.23 | Information security for use of cloud services |
| ISO27001 | ISO27001-A6.1 | Screening |
| ISO27001 | ISO27001-A8.2 | Privileged access rights |
| ISO27001 | ISO27001-A8.15 | Logging |
| ISO27001 | ISO27001-A8.16 | Monitoring activities |

### 4. HTTP Layer

#### Plan Gating Dependency

**New in `adapters/http/api/auth/dependencies.py`:**

```python
def require_plan_feature(feature: str) -> Callable:
    """Factory returning a dependency that raises 402 if feature not available."""
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
            raise HTTPException(
                status_code=402,
                detail=f"Feature '{feature}' requires Enterprise plan",
            )
        return current_user
    return checker
```

#### Audit Router Endpoints

**`adapters/http/api/audit/routers.py`** — prefix `/api/v1/audit`, tags `["audit"]`

| Method | Route | Access | Description |
|--------|-------|--------|-------------|
| GET | `/api/v1/audit` | Admin + Enterprise | List audit entries (paginated, filtered) |
| GET | `/api/v1/audit/{id}` | Admin + Enterprise | Get audit entry detail with tags |
| POST | `/api/v1/audit/export` | Admin + Enterprise | Request async export (returns task_id) |
| GET | `/api/v1/audit/export/{task_id}/download` | Admin + Enterprise | Get signed download URL |
| POST | `/api/v1/audit/{id}/tags` | Admin + Enterprise | Add compliance tags to entry |
| DELETE | `/api/v1/audit/{id}/tags/{tag_id}` | Admin + Enterprise | Remove tag from entry |
| GET | `/api/v1/audit/controls` | Admin + Enterprise | List compliance controls |
| POST | `/api/v1/audit/controls` | Admin + Enterprise | Create custom control |
| PUT | `/api/v1/audit/controls/{id}` | Admin + Enterprise | Update custom control |
| DELETE | `/api/v1/audit/controls/{id}` | Admin + Enterprise | Deactivate custom control |

All endpoints use `Depends(require_plan_feature("audit_trail"))` combined with `require_role(UserRole.ADMIN)`.

**Super admin endpoint** (added to existing super admin router):

| Method | Route | Access | Description |
|--------|-------|--------|-------------|
| GET | `/api/v1/super-admin/audit` | Super Admin | Cross-company audit log (paginated, filtered) |

#### Schemas

**`adapters/http/api/audit/schemas.py`:**

```python
# Request schemas
class AuditListParams:  # Query params, not body
    page: int = 1
    page_size: int = 20
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    control_id: Optional[str] = None
    search: Optional[str] = None

class ExportAuditRequest(BaseModel):
    format: str  # "csv" or "pdf"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    control_id: Optional[str] = None

class AddAuditTagsRequest(BaseModel):
    control_ids: list[str]

class CreateControlRequest(BaseModel):
    code: str
    name: str
    framework: str
    description: Optional[str] = None

class UpdateControlRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Response schemas
class AuditEntryListResponse(BaseModel):
    id: str
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    response_status: int
    ip_address: Optional[str]
    created_at: Optional[datetime]
    tag_count: int

class AuditTagResponse(BaseModel):
    id: str
    control_id: str
    control_code: str
    control_name: str
    framework: str
    tagged_by: str
    tagged_at: Optional[datetime]

class AuditEntryDetailResponse(BaseModel):
    id: str
    company_id: Optional[str]
    actor_id: Optional[str]
    actor_email: str
    actor_name: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    http_method: str
    http_path: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[dict]
    response_status: int
    changes: Optional[dict]
    hash: str
    created_at: Optional[datetime]
    tags: list[AuditTagResponse]

class ComplianceControlResponse(BaseModel):
    id: str
    code: str
    name: str
    framework: str
    description: Optional[str]
    is_predefined: bool
    is_active: bool
    created_at: Optional[datetime]

class ExportStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    download_url: Optional[str] = None
```

#### Dependencies

**`adapters/http/api/audit/dependencies.py`:**

```python
def get_audit_repo(db: Session = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
```

### 5. Celery Task

**`core/tasks/audit.py`:**

```python
@celery_app.task(
    name="core.tasks.audit.export_audit_log",
    bind=True,
    max_retries=3,
)
def export_audit_log(self, company_id, requested_by, format, filters):
    """Export audit log as CSV or PDF and upload to MinIO."""
    # 1. Query audit entries with filters (no pagination — fetch all)
    # 2. Generate CSV (csv.writer) or PDF (Jinja2 + WeasyPrint)
    # 3. Upload to MinIO: audit-exports/{company_id}/{task_id}.{ext}
    # 4. Create notification with download URL
```

- Register in `core/tasks/__init__.py`
- Add `AUDIT_EXPORT_READY` to `EventType` enum
- Export template: `templates/reports/audit_export.html`

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/auth/dependencies.py` | Add function | `require_plan_feature()` dependency factory |
| `src/notification_bc/notification/domain/enums.py` | Add value | `AUDIT_EXPORT_READY` event type |
| `core/tasks/__init__.py` | Add import | Register `export_audit_log` task |
| `app.py` | Add import + include | Register audit router |
| `adapters/http/api/super_admin/routers.py` | Add endpoint | Cross-company audit GET |
| `adapters/http/api/super_admin/dependencies.py` | Add function | `get_audit_repo` if not shared |
| `templates/reports/audit_export.html` | New file | PDF export template |

### 7. Frontend

#### Pages

| Page | File | Description |
|------|------|-------------|
| Audit Log | `web/app/src/pages/admin/AuditLogPage.tsx` | Paginated table with date range picker, filters, export button |
| Audit Detail | `web/app/src/pages/admin/AuditEntryDetailPage.tsx` | Full metadata, JSON diff viewer, compliance tag management |
| Compliance Controls | `web/app/src/pages/admin/ComplianceControlsPage.tsx` | Table with predefined + custom controls, create/edit/deactivate |
| Cross-Company Audit | `web/app/src/pages/superadmin/CrossCompanyAuditPage.tsx` | Super admin view with company filter |

#### Routing & Navigation

- `web/app/src/router.tsx` — Add `/audit`, `/audit/:id`, `/settings/compliance`, `/super-admin/audit`
- `web/app/src/components/layout/Sidebar.tsx` — Add "Audit Log" under Security section (admin), "Compliance Controls" under Configuration, "Audit" in super admin section
- `web/app/src/types/index.ts` — Add `AuditEntry`, `AuditEntryDetail`, `ComplianceControl`, `AuditTag` interfaces

#### i18n

~50 keys across `en.ts` and `es.ts` for audit log, detail, export, compliance, super admin views.

## Database Schema

```sql
CREATE TABLE compliance_controls (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) REFERENCES companies(id),  -- NULL = predefined
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    framework VARCHAR(50) NOT NULL,
    description TEXT,
    is_predefined BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_compliance_controls_company_code UNIQUE (company_id, code)
);

CREATE INDEX ix_compliance_controls_company ON compliance_controls(company_id);
CREATE INDEX ix_compliance_controls_framework ON compliance_controls(framework);

CREATE TABLE audit_entry_tags (
    id VARCHAR(26) PRIMARY KEY,
    audit_entry_id VARCHAR(26) NOT NULL REFERENCES audit_entries(id),
    control_id VARCHAR(26) NOT NULL REFERENCES compliance_controls(id),
    tagged_by VARCHAR(26) NOT NULL REFERENCES users(id),
    tagged_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_audit_entry_tags_entry_control UNIQUE (audit_entry_id, control_id)
);

CREATE INDEX ix_audit_entry_tags_entry ON audit_entry_tags(audit_entry_id);
CREATE INDEX ix_audit_entry_tags_control ON audit_entry_tags(control_id);
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F0 (Audit Foundation) | Feature | AuditEntry entity, model, repository, middleware |
| PlanGate | Existing | Feature gating for Enterprise plan |
| S3StorageService | Existing | MinIO upload for export files |
| Celery | Existing | Async export task execution |
| WeasyPrint | Existing | PDF generation (same as reports) |
| Notification BC | Existing | Export-ready notification |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | ComplianceControl.create(), AuditEntryTag.create() | High |
| Unit | All 5 command handlers (create/update/deactivate control, add/remove tags) | High |
| Unit | All 3 query handlers (list entries, get detail, list controls) | High |
| Integration | 10 audit endpoints (CRUD, export, tags) | High |
| Integration | Super admin cross-company endpoint | High |
| Integration | Plan gating (402 for non-Enterprise) | Medium |
| Integration | Export task (CSV generation) | Medium |

## Implementation Order

1. Domain: Entities (ComplianceControl, AuditEntryTag) + exceptions
2. Infrastructure: Models + migration (with predefined controls seed)
3. Domain: Repository interface extensions
4. Infrastructure: Repository implementation (9 new methods)
5. Application: 3 query handlers + DTOs
6. Application: 5 command handlers
7. HTTP: require_plan_feature dependency
8. HTTP: Audit router (schemas, dependencies, 10 endpoints)
9. HTTP: Super admin cross-company endpoint
10. Celery: Export task + template + notification event type
11. Collateral: app.py router registration, tasks __init__.py
12. Tests: Unit tests (entities, commands, queries)
13. Tests: Integration tests (endpoints, plan gating)
14. Frontend: Types, routing, sidebar
15. Frontend: Audit log page, detail page, compliance controls page, super admin page
16. Frontend: i18n (EN + ES)

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large audit log exports timing out | Low | Medium | Celery async task with retry; no timeout concern |
| Predefined controls migration conflicts | Low | Low | Use unique revision ID; controls are insert-only |
| Plan gating missing on some endpoint | Medium | Medium | All endpoints use same dependency; integration test verifies 402 |
