# Implementation Tasks: F3 — Affected Assets & SLA Escalation

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-26
**Total Tasks:** 22
**Estimated Complexity:** M-L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Entities | 1 | S |
| Domain - Interfaces | 2 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 2 | S-M |
| Application - Commands | 2 | M |
| Application - Queries | 3 | M-L |
| HTTP - Schemas | 3 | S |
| HTTP - Routers & Dependencies | 3 | M |
| HTTP - Configuration | 1 | S |
| Tests - Unit | 5 | M |
| Tests - Integration | 3 | M |
| Frontend | 3 | M |

---

## Phase 1: Domain Layer

### TASK-001: Create CompanySlaEscalationConfig Entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create the SLA escalation config entity following the `nav_config` pattern.

**File:** `src/company_bc/sla_escalation_config/domain/entities.py`

**Implementation:**
```python
@dataclass
class CompanySlaEscalationConfig:
    id: str
    company_id: str
    enabled: bool  # default: True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id: str, enabled: bool = True) -> "CompanySlaEscalationConfig":
        return cls(id=str(ulid.new()), company_id=company_id, enabled=enabled)
```

**Acceptance Criteria:**
- [x] Dataclass with id, company_id, enabled, created_at, updated_at
- [x] `create()` factory method with `enabled=True` default
- [x] ULID-based ID generation
- [x] `__init__.py` files created for `sla_escalation_config/`, `domain/`

---

### TASK-002: Create SlaEscalationConfigRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the repository interface for SLA escalation config.

**File:** `src/company_bc/sla_escalation_config/domain/repository.py`

**Implementation:**
```python
class SlaEscalationConfigRepositoryInterface(ABC):
    @abstractmethod
    def save(self, config: CompanySlaEscalationConfig) -> CompanySlaEscalationConfig: ...

    @abstractmethod
    def find_by_company(self, company_id: str) -> Optional[CompanySlaEscalationConfig]: ...
```

**Acceptance Criteria:**
- [x] ABC interface with `save()` and `find_by_company()` methods
- [x] Uses `CompanySlaEscalationConfig` entity in signatures

---

### TASK-003: Add `find_by_ids()` to AssetRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Extend the existing AssetRepositoryInterface with a batch lookup method.

**File:** `src/asset_bc/asset/domain/repository.py`

**Implementation:**
Add to `AssetRepositoryInterface`:
```python
@abstractmethod
def find_by_ids(self, asset_ids: list[str], company_id: str) -> list[Asset]: ...
```

**Acceptance Criteria:**
- [x] New abstract method `find_by_ids(asset_ids, company_id)` added
- [x] Returns `list[Asset]`
- [x] No changes to existing methods

---

## Phase 2: Infrastructure Layer

### TASK-004: Create SlaEscalationConfigModel

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the SQLAlchemy model for the SLA escalation config table.

**File:** `src/company_bc/sla_escalation_config/infrastructure/models.py`

**Implementation:**
```python
class SlaEscalationConfigModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_sla_escalation_configs"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    __table_args__ = (UniqueConstraint("company_id", name="uq_sla_escalation_config_company"),)
```

**Acceptance Criteria:**
- [x] Uses `Mapped[type]` annotations (SQLAlchemy 2.0 style)
- [x] Inherits `ULIDMixin`, `TimestampMixin`, `Base`
- [x] `UniqueConstraint` on `company_id`
- [x] `company_id` column with FK to companies, indexed
- [x] `enabled` column with `server_default="true"`
- [x] `__init__.py` file created for `infrastructure/`

---

### TASK-005: Create Migration for `company_sla_escalation_configs`

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create Alembic migration for the SLA escalation config table.

**File:** `alembic/versions/e38c1_create_sla_escalation_config_table.py`

**Schema:**
```sql
CREATE TABLE company_sla_escalation_configs (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_sla_escalation_config_company UNIQUE (company_id)
);
CREATE INDEX ix_sla_escalation_config_company ON company_sla_escalation_configs(company_id);
```

**Acceptance Criteria:**
- [x] Revision ID: `e38c1`, revises: `e38b1`
- [x] All columns from schema
- [x] Index on company_id
- [x] Unique constraint on company_id
- [x] Reversible (downgrade drops table and index)

---

### TASK-006: Create SlaEscalationConfigRepository

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-002, TASK-004

**Description:**
Implement the repository for SLA escalation config following `nav_config` repository pattern.

**File:** `src/company_bc/sla_escalation_config/infrastructure/repository.py`

**Implementation:**
- `save()`: upsert — check for existing by company_id, update if found, insert if not
- `find_by_company()`: query by company_id, return entity or None
- `_to_entity()`: convert model to domain entity

**Acceptance Criteria:**
- [x] Implements `SlaEscalationConfigRepositoryInterface`
- [x] Upsert pattern on `save()` (check existing, update or insert)
- [x] `find_by_company()` returns `Optional[CompanySlaEscalationConfig]`
- [x] Proper model ↔ entity conversion

---

### TASK-007: Implement `find_by_ids()` in AssetRepository

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Implement the batch asset lookup using a single `WHERE id IN (...)` query.

**File:** `src/asset_bc/asset/infrastructure/repository.py`

**Implementation:**
```python
def find_by_ids(self, asset_ids: list[str], company_id: str) -> list[Asset]:
    if not asset_ids:
        return []
    stmt = select(AssetModel).where(
        AssetModel.company_id == company_id,
        AssetModel.id.in_(asset_ids),
    )
    models = self.session.execute(stmt).scalars().all()
    return [self._to_entity(m) for m in models]
```

**Acceptance Criteria:**
- [x] Returns empty list for empty `asset_ids`
- [x] Single query with `WHERE id IN (...) AND company_id = ...`
- [x] Uses existing `_to_entity()` conversion
- [x] No N+1 queries

---

## Phase 3: Application Layer

### TASK-008: Create SaveSlaEscalationConfigCommand + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-006

**Description:**
Create the command to save (upsert) SLA escalation configuration.

**File:** `src/company_bc/sla_escalation_config/application/commands/save_config.py`

**Implementation:**
```python
@dataclass
class SaveSlaEscalationConfigCommand(Command):
    company_id: str
    enabled: bool
    performed_by: str

class SaveSlaEscalationConfigCommandHandler(CommandHandler[SaveSlaEscalationConfigCommand]):
    def __init__(self, config_repo: SlaEscalationConfigRepositoryInterface):
        self.config_repo = config_repo

    def handle(self, command: SaveSlaEscalationConfigCommand) -> None:
        existing = self.config_repo.find_by_company(command.company_id)
        if existing:
            existing.enabled = command.enabled
            self.config_repo.save(existing)
        else:
            config = CompanySlaEscalationConfig.create(
                company_id=command.company_id,
                enabled=command.enabled,
            )
            self.config_repo.save(config)
```

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler`
- [x] Command + handler in same file
- [x] Handler returns None
- [x] Upserts: updates existing config or creates new one
- [x] `__init__.py` files created for `application/`, `commands/`

---

### TASK-009: Create GetSlaEscalationConfigQuery + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-006

**Description:**
Create the query to fetch SLA escalation config, returning default (enabled=True) when none exists.

**File:** `src/company_bc/sla_escalation_config/application/queries/get_config.py`

**Implementation:**
```python
@dataclass
class SlaEscalationConfigDto:
    enabled: bool

@dataclass
class GetSlaEscalationConfigQuery(Query):
    company_id: str

class GetSlaEscalationConfigQueryHandler(QueryHandler[GetSlaEscalationConfigQuery, SlaEscalationConfigDto]):
    def __init__(self, config_repo: SlaEscalationConfigRepositoryInterface):
        self.config_repo = config_repo

    def handle(self, query: GetSlaEscalationConfigQuery) -> SlaEscalationConfigDto:
        config = self.config_repo.find_by_company(query.company_id)
        if config:
            return SlaEscalationConfigDto(enabled=config.enabled)
        return SlaEscalationConfigDto(enabled=True)  # default
```

**Acceptance Criteria:**
- [x] Inherits from `Query` / `QueryHandler`
- [x] Query + handler + DTO in same file
- [x] Returns `SlaEscalationConfigDto(enabled=True)` when no config exists
- [x] `__init__.py` file created for `queries/`

---

### TASK-010: Create SetAffectedAssetsCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003, TASK-007

**Description:**
Create the command to save affected asset IDs into `request.data["affected_asset_ids"]`.

**File:** `src/request_bc/request/application/commands/set_affected_assets.py`

**Implementation:**
Command fields: `request_id`, `company_id`, `asset_ids: list[str]`, `performed_by`

Handler logic:
1. Fetch request by ID — raise `RequestNotFoundError` if not found
2. Validate all asset_ids exist in company via `find_by_ids` — raise `AssetNotFoundError` for missing
3. Merge `affected_asset_ids` into `request.data` (preserve existing data keys)
4. Save request
5. Record `RequestEvent` with type `affected_assets_updated`

Domain exceptions:
- `RequestNotFoundError`
- `AssetNotFoundError`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler`
- [x] Command + handler in same file
- [x] Handler returns None
- [x] Validates request exists (404)
- [x] Validates all asset IDs exist in company (404)
- [x] Merges `affected_asset_ids` into `request.data` (doesn't overwrite other data keys)
- [x] Records `RequestEvent` "affected_assets_updated" with old and new asset IDs
- [x] Domain exceptions defined in same file

---

### TASK-011: Create GetRequesterAssetsQuery + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003, TASK-007

**Description:**
Create the query to fetch the requester's assigned assets with `is_affected` flag.

**File:** `src/request_bc/request/application/queries/get_requester_assets.py`

**Implementation:**
```python
@dataclass
class RequesterAssetDto:
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str]
    status: str
    is_affected: bool

@dataclass
class GetRequesterAssetsQuery(Query):
    request_id: str
    company_id: str
```

Handler logic:
1. Fetch request — return empty list if not found
2. Get `created_by` (requester user ID) from request
3. Use `asset_repo.find_by_assigned_to(created_by, company_id)` to get requester's assets
4. Read `request.data.get("affected_asset_ids", [])` for current affected IDs
5. Map to `RequesterAssetDto` list with `is_affected` flag

**Acceptance Criteria:**
- [x] Inherits from `Query` / `QueryHandler`
- [x] Query + handler + DTO in same file
- [x] Returns `list[RequesterAssetDto]`
- [x] Returns empty list when request not found
- [x] Correctly sets `is_affected` based on `data.affected_asset_ids`
- [x] Uses `find_by_assigned_to` (no N+1)

---

### TASK-012: Modify GetRequestSlaStatusQuery with Escalation Logic

**Phase:** Application
**Complexity:** L
**Dependencies:** TASK-007, TASK-009

**Description:**
Add criticality-based SLA escalation to the existing SLA status query.

**File:** `src/sla_bc/sla/application/queries/get_request_sla.py`

**Modifications:**

1. Add new constructor dependencies:
   - `asset_repo: AssetRepositoryInterface` (default: `None`)
   - `escalation_config_repo: SlaEscalationConfigRepositoryInterface` (default: `None`)

2. Add new DTO fields to `SlaStatusDto`:
   ```python
   escalated: bool = False
   effective_priority: Optional[str] = None
   original_priority: Optional[str] = None
   ```

3. Add escalation pure functions:
   ```python
   PRIORITY_ESCALATION_MAP = {
       "low": "medium",
       "medium": "high",
       "high": "urgent",
       "urgent": "urgent",
   }

   def compute_effective_priority(
       request_priority: str,
       affected_asset_criticalities: list[str],
   ) -> tuple[str, bool]: ...

   def _highest_criticality(criticalities: list[str]) -> str: ...
   ```

4. Modify `handle()` logic:
   - After fetching request, check if escalation is enabled
   - If enabled: read `request.data.get("affected_asset_ids", [])`, fetch assets via `find_by_ids`, extract criticalities, compute effective priority
   - Use `effective_priority` (instead of `request.priority.value`) for policy lookup if escalated
   - Populate new DTO fields: `escalated`, `effective_priority`, `original_priority`

**Acceptance Criteria:**
- [x] New constructor deps are optional (default `None`) — backward compatible
- [x] New DTO fields have defaults — backward compatible
- [x] `compute_effective_priority()` pure function with all escalation rules
- [x] CRITICAL asset: escalates one level (LOW→MEDIUM, MEDIUM→HIGH, HIGH→URGENT)
- [x] CRITICAL asset + URGENT priority: no escalation (already max)
- [x] HIGH asset + LOW priority: escalates to MEDIUM
- [x] HIGH asset + MEDIUM/HIGH/URGENT: no escalation
- [x] MEDIUM/LOW asset: no escalation
- [x] No affected assets: no escalation
- [x] Escalation disabled: no escalation (respects company config)
- [x] Policy lookup uses `effective_priority` when escalated
- [x] DTO includes `original_priority`, `effective_priority`, `escalated`

---

## Phase 4: HTTP Layer

### TASK-013: Add Request Schemas for Affected Assets

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Add Pydantic schemas for the affected assets endpoints.

**File:** `adapters/http/api/requests/schemas.py`

**Implementation:**
```python
class SetAffectedAssetsRequest(BaseModel):
    asset_ids: list[str]

class RequesterAssetResponse(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str] = None
    status: str
    is_affected: bool
```

**Acceptance Criteria:**
- [x] `SetAffectedAssetsRequest` with `asset_ids: list[str]`
- [x] `RequesterAssetResponse` with all fields from design

---

### TASK-014: Create SLA Escalation Config Schemas + Dependencies

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Create schemas and dependency injection for the SLA escalation config endpoints.

**Files:**
- `adapters/http/api/settings/sla_escalation_schemas.py`
- `adapters/http/api/settings/sla_escalation_dependencies.py`

**Implementation:**
```python
# schemas
class SaveSlaEscalationConfigRequest(BaseModel):
    enabled: bool

class SlaEscalationConfigResponse(BaseModel):
    enabled: bool

# dependencies
def get_sla_escalation_config_repo(db: Session = Depends(get_db)):
    return SlaEscalationConfigRepository(db)
```

**Acceptance Criteria:**
- [x] Request schema with `enabled: bool`
- [x] Response schema with `enabled: bool`
- [x] Dependency returns `SlaEscalationConfigRepository(db)`

---

### TASK-015: Add SLA Response Escalation Fields

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-012

**Description:**
Add escalation fields to the SLA status response in the SLA router.

**File:** `adapters/http/api/sla/routers.py`

**Modifications:**
Add to the SLA status response dict (in `get_request_sla_status` endpoint):
```python
"escalated": dto.escalated,
"effective_priority": dto.effective_priority,
"original_priority": dto.original_priority,
```

**Acceptance Criteria:**
- [x] Response includes `escalated`, `effective_priority`, `original_priority`
- [x] Backward compatible (new fields have defaults)

---

### TASK-016: Add PATCH affected-assets + GET requester-assets Endpoints

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-010, TASK-011, TASK-013

**Description:**
Add two new endpoints to the requests router.

**File:** `adapters/http/api/requests/routers.py`

**Endpoints:**

1. `PATCH /api/v1/requests/{request_id}/affected-assets`
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Body: `SetAffectedAssetsRequest`
   - Catches: `RequestNotFoundError` → 404, `AssetNotFoundError` → 404
   - Returns refreshed request response

2. `GET /api/v1/requests/{request_id}/requester-assets`
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Returns: `list[RequesterAssetResponse]`

**Acceptance Criteria:**
- [x] PATCH endpoint saves affected asset IDs
- [x] PATCH catches `RequestNotFoundError` → 404
- [x] PATCH catches `AssetNotFoundError` → 404
- [x] GET endpoint returns requester's assigned assets with `is_affected` flag
- [x] Both require technician+ role

---

### TASK-017: Create SLA Escalation Config Router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-008, TASK-009, TASK-014

**Description:**
Create the settings router for SLA escalation config, following `nav_config_router.py` pattern.

**File:** `adapters/http/api/settings/sla_escalation_router.py`

**Endpoints:**

1. `GET /api/v1/settings/sla-escalation`
   - Auth: `require_role(UserRole.ADMIN)`
   - Returns: `SlaEscalationConfigResponse`

2. `PUT /api/v1/settings/sla-escalation`
   - Auth: `require_role(UserRole.ADMIN)`
   - Body: `SaveSlaEscalationConfigRequest`
   - Returns: `SlaEscalationConfigResponse`

**Acceptance Criteria:**
- [x] GET returns current config (or default `enabled: true`)
- [x] PUT upserts config and returns updated value
- [x] Both require admin role

---

### TASK-018: Update SLA Router DI + Register Routers

**Phase:** HTTP / Configuration
**Complexity:** S
**Dependencies:** TASK-012, TASK-015, TASK-017

**Description:**
Update the SLA router to pass new dependencies to the handler, and register the escalation config router.

**Files:**
- `adapters/http/api/sla/routers.py` — update `get_request_sla_status` endpoint DI
- `adapters/http/api/sla/dependencies.py` — add `get_asset_repo` and `get_sla_escalation_config_repo`
- `app.py` — register `sla_escalation_router`

**Modifications in SLA router:**
```python
# Update endpoint to inject new dependencies
@router.get("/requests/{request_id}/status")
def get_request_sla_status(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    sla_repo: SlaRepository = Depends(get_sla_repo),
    request_repo=Depends(get_request_repo),
    asset_repo=Depends(get_asset_repo),
    escalation_config_repo=Depends(get_sla_escalation_config_repo),
):
    handler = GetRequestSlaStatusQueryHandler(
        sla_repo=sla_repo,
        request_repo=request_repo,
        asset_repo=asset_repo,
        escalation_config_repo=escalation_config_repo,
    )
    ...
```

**Acceptance Criteria:**
- [x] SLA status endpoint passes `asset_repo` and `escalation_config_repo` to handler
- [x] New dependency functions added to SLA dependencies
- [x] `sla_escalation_router` registered in app.py
- [x] SLA response includes new escalation fields

---

## Phase 5: Tests

### TASK-019: Unit Tests — SLA Escalation Logic

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-012

**Description:**
Test the `compute_effective_priority()` function with all priority × criticality combinations.

**File:** `tests/unit/sla_bc/sla/application/queries/test_sla_escalation.py`

**Test Cases:**
- CRITICAL asset: LOW→MEDIUM, MEDIUM→HIGH, HIGH→URGENT, URGENT→URGENT (no escalation)
- HIGH asset: LOW→MEDIUM, MEDIUM→MEDIUM (no), HIGH→HIGH (no), URGENT→URGENT (no)
- MEDIUM asset: no escalation for any priority
- LOW asset: no escalation for any priority
- Empty criticalities: no escalation
- Multiple criticalities: uses highest
- Escalation disabled: no escalation
- Modified SLA handler integration: verifies handler uses effective priority for policy lookup

**Acceptance Criteria:**
- [x] All 4×4 priority × criticality combinations tested
- [x] Empty affected assets tested
- [x] Multiple assets with mixed criticalities tested
- [x] `_highest_criticality` tested
- [x] Handler-level test with mocked repos verifying escalated policy lookup

---

### TASK-020: Unit Tests — SetAffectedAssetsCommand + GetRequesterAssetsQuery

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-010, TASK-011

**Description:**
Unit tests for the affected assets command and requester assets query.

**Files:**
- `tests/unit/request_bc/request/application/commands/test_set_affected_assets.py`
- `tests/unit/request_bc/request/application/queries/test_get_requester_assets.py`

**Test Cases (command):**
- Happy path: sets affected_asset_ids in request.data
- Request not found: raises `RequestNotFoundError`
- Asset not found: raises `AssetNotFoundError`
- Merges into existing data (doesn't overwrite other keys)
- Records RequestEvent "affected_assets_updated"

**Test Cases (query):**
- Happy path: returns requester's assets with is_affected flag
- Request not found: returns empty list
- No assigned assets: returns empty list
- Correctly identifies affected vs non-affected assets

**Acceptance Criteria:**
- [x] All command validation paths tested
- [x] Data merging behavior tested
- [x] Event recording verified
- [x] Query returns correct is_affected flags
- [x] Edge cases covered (no request, no assets)

---

### TASK-021: Unit Tests — SLA Escalation Config

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-008, TASK-009

**Description:**
Unit tests for the escalation config command and query.

**Files:**
- `tests/unit/company_bc/sla_escalation_config/test_commands.py`
- `tests/unit/company_bc/sla_escalation_config/test_queries.py`

**Test Cases (command):**
- Creates new config when none exists
- Updates existing config
- Sets enabled to false

**Test Cases (query):**
- Returns existing config
- Returns default (enabled=True) when none exists

**Acceptance Criteria:**
- [x] Create and update paths tested
- [x] Default value behavior tested

---

### TASK-022: Integration Tests — Affected Assets + SLA Escalation

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-016, TASK-017, TASK-018

**Description:**
Integration tests for all new endpoints.

**Files:**
- `tests/integration/test_affected_assets_endpoints.py`
- `tests/integration/test_sla_escalation_endpoints.py`

**Test Cases (affected assets):**
- PATCH sets affected asset IDs
- PATCH with invalid asset ID → 404
- PATCH with invalid request ID → 404
- GET requester assets with is_affected flags
- GET requester assets when no assets assigned

**Test Cases (SLA escalation):**
- SLA status shows escalated=true when critical asset is affected
- SLA status shows escalated=false with no affected assets
- SLA escalation config GET returns default (enabled: true)
- SLA escalation config PUT saves and returns updated value
- SLA status respects escalation config (disabled = no escalation)

**Acceptance Criteria:**
- [x] All CRUD paths tested end-to-end
- [x] Error cases validated (404)
- [x] SLA escalation verified with real policy lookup
- [x] Config toggle tested

---

## Phase 6: Frontend

### TASK-023: Add Affected Assets Section to RequestDetailPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-016

**Description:**
Add "Affected Assets" section on the request detail page for technicians.

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation:**
- Fetch requester assets from `GET /api/v1/requests/{id}/requester-assets`
- Display list of assets with: name (brand + model), type, serial number, criticality badge, status
- Checkbox per asset (checked = affected)
- On checkbox change, PATCH `/api/v1/requests/{id}/affected-assets` with updated asset_ids list
- Show "No assets assigned to requester" when list is empty
- Only visible to technician+ roles

**Acceptance Criteria:**
- [x] Section lists requester's assigned assets
- [x] Checkboxes toggle affected status
- [x] Criticality badge shown per asset
- [x] Auto-saves on checkbox change
- [x] "No assets assigned to requester" empty state

---

### TASK-024: Add SLA Escalation Indicator

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-015

**Description:**
Show "Escalated" indicator on the SLA status section when escalation is active.

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation:**
- Read `escalated`, `effective_priority`, `original_priority` from SLA status response
- When `escalated: true`, show badge: "Escalated: {original} → {effective}"
- Visual indicator (e.g., orange/amber badge)

**Acceptance Criteria:**
- [x] "Escalated" badge shown when `escalated: true`
- [x] Shows original and effective priority
- [x] Hidden when not escalated

---

### TASK-025: Add i18n Keys + Frontend Types

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-023, TASK-024

**Description:**
Add internationalization keys and TypeScript types.

**Files:**
- `web/app/src/locales/en.ts` — English keys
- `web/app/src/locales/es.ts` — Spanish keys
- `web/app/src/types/index.ts` — TypeScript types

**i18n Keys:**
- `affectedAssets.title`, `affectedAssets.noAssets`, `affectedAssets.save`, `affectedAssets.saved`
- `sla.escalated`, `sla.escalatedFrom`, `sla.effectivePriority`, `sla.originalPriority`

**Types:**
```typescript
interface RequesterAsset {
  id: string;
  brand: string;
  model: string;
  serial_number: string;
  type: string;
  criticality: string | null;
  status: string;
  is_affected: boolean;
}
```

**Acceptance Criteria:**
- [x] EN translations added
- [x] ES translations added
- [x] `RequesterAsset` type defined
- [x] SLA response type updated with escalation fields

---

## Dependency Graph

```
TASK-001 (Entity)
    ├── TASK-002 (Repo Interface) ──┐
    └── TASK-004 (Model) ───────────┤
                                    ├── TASK-006 (Repo Impl)
TASK-005 (Migration) ◄─────────────┘         │
                                    ┌────────┤
                                    ▼        ▼
                              TASK-008    TASK-009
                              (Save Cmd)  (Get Query)
                                    │        │
                                    ▼        ▼
                              TASK-017    TASK-018
                              (Config Router) (SLA DI)

TASK-003 (find_by_ids Interface)
    └── TASK-007 (find_by_ids Impl) ──┐
                                      ├── TASK-010 (SetAffectedAssets Cmd)
                                      ├── TASK-011 (GetRequesterAssets Query)
                                      └── TASK-012 (Modify SLA Query)
                                             │
                                             ▼
                                       TASK-015 (SLA Response Fields)
                                       TASK-016 (Request Endpoints)
                                       TASK-018 (SLA DI Update)

TASK-013 (Request Schemas) ◄── parallel, no deps

Tests: TASK-019..022 depend on their respective application/HTTP tasks
Frontend: TASK-023..25 depend on HTTP endpoints
```

## Execution Order

**Batch 1 (Parallel — Domain):** TASK-001, TASK-003, TASK-013
**Batch 2 (Parallel — Domain + Infra):** TASK-002, TASK-004, TASK-005, TASK-007
**Batch 3 (Parallel — Infra):** TASK-006
**Batch 4 (Parallel — Application):** TASK-008, TASK-009, TASK-010, TASK-011
**Batch 5 (Application — depends on TASK-009):** TASK-012
**Batch 6 (Parallel — HTTP):** TASK-014, TASK-015, TASK-016, TASK-017
**Batch 7 (HTTP — depends on TASK-012, TASK-017):** TASK-018
**Batch 8 (Parallel — Tests):** TASK-019, TASK-020, TASK-021, TASK-022
**Batch 9 (Parallel — Frontend):** TASK-023, TASK-024, TASK-025

## Final Checklist

- [x] All 25 tasks completed
- [x] `make test` — unit tests pass
- [x] `make test-integration` — integration tests pass
- [x] `npx tsc --noEmit` — TypeScript clean
- [x] `make lint` — mypy + flake8 pass
- [x] Escalation logic covers all priority × criticality combinations
- [x] SLA response backward compatible (new fields have defaults)
- [x] Company config defaults to enabled=true
