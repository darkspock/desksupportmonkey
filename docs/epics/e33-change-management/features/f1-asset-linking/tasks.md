# Implementation Tasks: Asset Linking

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-27
**Total Tasks:** 18
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | S |
| Domain - Repository Interface | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Migration | 1 | S |
| Infrastructure - Repository | 1 | S |
| Application - Commands | 2 | S-M |
| Application - Queries | 1 | S |
| HTTP - Schemas | 1 | S |
| HTTP - Dependencies | 1 | S |
| HTTP - Router | 1 | M |
| Tests - Unit | 2 | M |
| Tests - Integration | 1 | M |
| Frontend | 2 | S-M |

---

## Phase 1: Domain Layer

### TASK-001: Add ASSET_LINKED and ASSET_UNLINKED to ChangeEventType

**Phase:** Domain - Enums
**Complexity:** S
**Dependencies:** None

**File:** `src/change_bc/change_request/domain/enums.py` (modify)

**Implementation:**
Add two values to the existing `ChangeEventType` enum:
```python
ASSET_LINKED = "asset_linked"
ASSET_UNLINKED = "asset_unlinked"
```

**Acceptance Criteria:**
- [x] `ASSET_LINKED = "asset_linked"` added to ChangeEventType
- [x] `ASSET_UNLINKED = "asset_unlinked"` added to ChangeEventType

---

### TASK-002: Add asset linking exceptions

**Phase:** Domain - Exceptions
**Complexity:** S
**Dependencies:** None

**File:** `src/change_bc/change_request/domain/exceptions.py` (modify)

**Implementation:**
Add three new exception classes:
```python
class AssetAlreadyLinkedError(Exception): ...
class AssetNotLinkedError(Exception): ...
class ChangeNotUnlinkableError(Exception):
    """Unlinking only allowed in DRAFT, PENDING_APPROVAL, SCHEDULED."""
    ...
```

**Acceptance Criteria:**
- [x] `AssetAlreadyLinkedError` added
- [x] `AssetNotLinkedError` added
- [x] `ChangeNotUnlinkableError` added with docstring

---

### TASK-003: Add ChangeAsset entity

**Phase:** Domain - Entities
**Complexity:** S
**Dependencies:** None

**File:** `src/change_bc/change_request/domain/entities.py` (modify)

**Implementation:**
Add `ChangeAsset` dataclass to the existing entities file:
```python
@dataclass
class ChangeAsset:
    id: str
    change_request_id: str
    asset_id: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, change_request_id: str, asset_id: str) -> "ChangeAsset":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            asset_id=asset_id,
        )
```

**Acceptance Criteria:**
- [x] `ChangeAsset` dataclass with 4 fields (id, change_request_id, asset_id, created_at)
- [x] `create()` class method generates ULID and returns instance

---

### TASK-004: Add asset methods to ChangeRequestRepositoryInterface

**Phase:** Domain - Repository Interface
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/change_bc/change_request/domain/repository.py` (modify)

**Implementation:**
Add three abstract methods to the existing `ChangeRequestRepositoryInterface`:
```python
# ChangeAsset
@abstractmethod
def save_change_asset(self, change_asset: ChangeAsset) -> None: ...

@abstractmethod
def delete_change_asset(self, change_request_id: str, asset_id: str) -> None: ...

@abstractmethod
def find_assets_by_change(self, change_request_id: str) -> list[ChangeAsset]: ...
```

**Acceptance Criteria:**
- [x] `save_change_asset(change_asset: ChangeAsset) -> None` abstract method added
- [x] `delete_change_asset(change_request_id: str, asset_id: str) -> None` abstract method added
- [x] `find_assets_by_change(change_request_id: str) -> list[ChangeAsset]` abstract method added
- [x] Import for `ChangeAsset` entity added

---

## Phase 2: Infrastructure Layer

### TASK-005: Add ChangeAssetModel

**Phase:** Infrastructure - Models
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/change_bc/change_request/infrastructure/models.py` (modify)

**Implementation:**
Add `ChangeAssetModel` to the existing models file:
```python
class ChangeAssetModel(ULIDMixin, Base):
    __tablename__ = "change_assets"

    change_request_id: Mapped[str] = mapped_column(
        String(26), ForeignKey("change_requests.id"), nullable=False, index=True
    )
    asset_id: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("change_request_id", "asset_id", name="uq_change_assets_change_asset"),
        Index("ix_change_assets_asset_id", "asset_id"),
    )
```

**Acceptance Criteria:**
- [x] `ChangeAssetModel` with `Mapped[]` annotations (SQLAlchemy 2.0 style)
- [x] FK to `change_requests.id`
- [x] `UniqueConstraint("change_request_id", "asset_id")`
- [x] Index on `asset_id`
- [x] `server_default=func.now()` on `created_at`
- [x] No FK to assets table (cross-BC, string only)

---

### TASK-006: Create change_assets migration

**Phase:** Infrastructure - Migration
**Complexity:** S
**Dependencies:** TASK-005

**File:** `alembic/versions/e33b1_create_change_assets_table.py` (new)

**Implementation:**
Create Alembic migration:
```sql
CREATE TABLE change_assets (
    id VARCHAR(26) PRIMARY KEY,
    change_request_id VARCHAR(26) NOT NULL REFERENCES change_requests(id),
    asset_id VARCHAR(26) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_change_assets_change_asset UNIQUE (change_request_id, asset_id)
);

CREATE INDEX ix_change_assets_change_request_id ON change_assets (change_request_id);
CREATE INDEX ix_change_assets_asset_id ON change_assets (asset_id);
```

**Acceptance Criteria:**
- [x] Table `change_assets` created with all columns
- [x] FK to `change_requests(id)`
- [x] UniqueConstraint on `(change_request_id, asset_id)`
- [x] Indexes on `change_request_id` and `asset_id`
- [x] Reversible (downgrade drops table)
- [x] Depends on F0 migration (`e33a1`)

---

### TASK-007: Implement asset repository methods

**Phase:** Infrastructure - Repository
**Complexity:** S
**Dependencies:** TASK-004, TASK-005

**File:** `src/change_bc/change_request/infrastructure/repository.py` (modify)

**Implementation:**
Add three method implementations to `ChangeRequestRepository`:

```python
def save_change_asset(self, change_asset: ChangeAsset) -> None:
    model = ChangeAssetModel(
        id=change_asset.id,
        change_request_id=change_asset.change_request_id,
        asset_id=change_asset.asset_id,
    )
    self.session.add(model)
    self.session.flush()

def delete_change_asset(self, change_request_id: str, asset_id: str) -> None:
    self.session.query(ChangeAssetModel).filter(
        ChangeAssetModel.change_request_id == change_request_id,
        ChangeAssetModel.asset_id == asset_id,
    ).delete()
    self.session.flush()

def find_assets_by_change(self, change_request_id: str) -> list[ChangeAsset]:
    models = self.session.execute(
        select(ChangeAssetModel).where(
            ChangeAssetModel.change_request_id == change_request_id
        )
    ).scalars().all()
    return [
        ChangeAsset(
            id=m.id,
            change_request_id=m.change_request_id,
            asset_id=m.asset_id,
            created_at=m.created_at,
        )
        for m in models
    ]
```

**Acceptance Criteria:**
- [x] `save_change_asset()` — adds model and flushes
- [x] `delete_change_asset()` — filters by both IDs and deletes
- [x] `find_assets_by_change()` — returns list of ChangeAsset domain entities
- [x] Imports for `ChangeAssetModel`, `ChangeAsset` added

---

## Phase 3: Application Layer

### TASK-008: Create LinkAssetsCommand + handler

**Phase:** Application - Commands
**Complexity:** M
**Dependencies:** TASK-001, TASK-003, TASK-004

**File:** `src/change_bc/change_request/application/commands/link_assets.py` (new)

**Implementation:**
```python
@dataclass
class LinkAssetsCommand(Command):
    change_id: str
    company_id: str
    asset_ids: list[str]
    actor_id: str

class LinkAssetsCommandHandler(CommandHandler[LinkAssetsCommand]):
    def __init__(self, change_repo, asset_repo):
        self.change_repo = change_repo
        self.asset_repo = asset_repo

    def handle(self, command: LinkAssetsCommand) -> None:
        # 1. Find change request, raise ChangeNotFoundError if missing
        # 2. Guard: raise InvalidStatusTransitionError if terminal
        # 3. Fetch existing links, build set of existing asset_ids
        # 4. For each asset_id:
        #    - Skip if already linked (duplicate)
        #    - Validate asset exists via asset_repo.find_by_id()
        #    - Skip if asset not found
        #    - Create ChangeAsset.create() and save
        # 5. If linked > 0, create ChangeEvent with ASSET_LINKED
```

**Acceptance Criteria:**
- [x] `LinkAssetsCommand` inherits from `Command` with fields: change_id, company_id, asset_ids, actor_id
- [x] `LinkAssetsCommandHandler` inherits from `CommandHandler[LinkAssetsCommand]`
- [x] Constructor takes `change_repo: ChangeRequestRepositoryInterface` and `asset_repo: AssetRepositoryInterface`
- [x] Raises `ChangeNotFoundError` if change not found
- [x] Raises `InvalidStatusTransitionError` if change in terminal state
- [x] Silently skips duplicate asset links
- [x] Validates each asset exists via cross-BC `asset_repo.find_by_id(asset_id, company_id)`
- [x] Silently skips assets that don't exist
- [x] Creates `ChangeAsset.create()` for each valid link
- [x] Creates single `ChangeEvent` with `ASSET_LINKED` type if any linked
- [x] Event metadata includes `asset_ids` and `linked` count

---

### TASK-009: Create UnlinkAssetCommand + handler

**Phase:** Application - Commands
**Complexity:** S
**Dependencies:** TASK-001, TASK-002, TASK-004

**File:** `src/change_bc/change_request/application/commands/unlink_asset.py` (new)

**Implementation:**
```python
@dataclass
class UnlinkAssetCommand(Command):
    change_id: str
    company_id: str
    asset_id: str
    actor_id: str

class UnlinkAssetCommandHandler(CommandHandler[UnlinkAssetCommand]):
    def __init__(self, change_repo):
        self.change_repo = change_repo

    def handle(self, command: UnlinkAssetCommand) -> None:
        # 1. Find change request, raise ChangeNotFoundError if missing
        # 2. Guard: only DRAFT, PENDING_APPROVAL, SCHEDULED allowed
        #    Raise ChangeNotUnlinkableError otherwise
        # 3. delete_change_asset(change_id, asset_id)
        # 4. Create ChangeEvent with ASSET_UNLINKED
```

**Acceptance Criteria:**
- [x] `UnlinkAssetCommand` inherits from `Command` with fields: change_id, company_id, asset_id, actor_id
- [x] `UnlinkAssetCommandHandler` inherits from `CommandHandler[UnlinkAssetCommand]`
- [x] Constructor takes `change_repo: ChangeRequestRepositoryInterface`
- [x] Raises `ChangeNotFoundError` if change not found
- [x] Raises `ChangeNotUnlinkableError` if status not in `{DRAFT, PENDING_APPROVAL, SCHEDULED}`
- [x] Calls `delete_change_asset(change_id, asset_id)`
- [x] Creates `ChangeEvent` with `ASSET_UNLINKED` type
- [x] Event metadata includes `asset_id`

---

### TASK-010: Extend detail query with affected assets

**Phase:** Application - Queries
**Complexity:** S
**Dependencies:** TASK-003, TASK-004

**File:** `src/change_bc/change_request/application/queries/get_change_request_detail.py` (modify)

**Implementation:**

1. Add `ChangeAssetDto` dataclass:
```python
@dataclass
class ChangeAssetDto:
    id: str
    asset_id: str
    asset_name: Optional[str]
    asset_tag: Optional[str]
    asset_brand: Optional[str]
    asset_model: Optional[str]
    created_at: Optional[datetime]
```

2. Add `affected_assets: list[ChangeAssetDto]` field to `ChangeRequestDetailDto`

3. Add optional `asset_repo` parameter to `GetChangeRequestDetailQueryHandler.__init__`

4. In `handle()`, after fetching events:
   - If `asset_repo` is set, fetch `change_assets` via `find_assets_by_change()`
   - Resolve asset details (name, tag, brand, model) via cross-BC `asset_repo.find_by_id()`
   - Build `ChangeAssetDto` list
   - Include in returned `ChangeRequestDetailDto`

**Acceptance Criteria:**
- [x] `ChangeAssetDto` dataclass with 7 fields
- [x] `affected_assets: list[ChangeAssetDto]` added to `ChangeRequestDetailDto`
- [x] `asset_repo` parameter added to handler `__init__` (optional, default None)
- [x] Assets fetched from `change_repo.find_assets_by_change()`
- [x] Asset details resolved via `asset_repo.find_by_id(aid, company_id)`
- [x] Graceful handling if asset not found (name/tag/brand/model = None)

---

## Phase 4: HTTP Layer

### TASK-011: Add asset linking schemas

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** None

**File:** `adapters/http/api/changes/schemas.py` (modify)

**Implementation:**

1. Add request schema:
```python
class LinkAssetsRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1)
```

2. Add response schema:
```python
class ChangeAssetResponse(BaseModel):
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_brand: Optional[str] = None
    asset_model: Optional[str] = None
    created_at: Optional[datetime] = None
```

3. Extend `ChangeRequestDetailResponse`:
```python
affected_assets: list[ChangeAssetResponse] = []
```

**Acceptance Criteria:**
- [x] `LinkAssetsRequest` with `asset_ids: list[str]` (min_length=1)
- [x] `ChangeAssetResponse` with 7 fields
- [x] `ChangeRequestDetailResponse` extended with `affected_assets: list[ChangeAssetResponse] = []`

---

### TASK-012: Add asset_repo dependency

**Phase:** HTTP - Dependencies
**Complexity:** S
**Dependencies:** None

**File:** `adapters/http/api/changes/dependencies.py` (modify)

**Implementation:**
```python
from src.asset_bc.asset.infrastructure.repository import AssetRepository

def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)
```

**Acceptance Criteria:**
- [x] `get_asset_repo` function returns `AssetRepository` instance
- [x] Depends on `get_db` session

---

### TASK-013: Add link/unlink endpoints and extend detail route

**Phase:** HTTP - Router
**Complexity:** M
**Dependencies:** TASK-008, TASK-009, TASK-010, TASK-011, TASK-012

**File:** `adapters/http/api/changes/routers.py` (modify)

**Implementation:**

1. Add `POST /{change_id}/assets` endpoint:
   - Auth: `require_roles(TECHNICIAN)`
   - Body: `LinkAssetsRequest`
   - Handler: `LinkAssetsCommandHandler(change_repo, asset_repo)`
   - Returns: `204 No Content`
   - Errors: 404 (ChangeNotFoundError), 422 (InvalidStatusTransitionError)

2. Add `DELETE /{change_id}/assets/{asset_id}` endpoint:
   - Auth: `require_roles(TECHNICIAN)`
   - Handler: `UnlinkAssetCommandHandler(change_repo)`
   - Returns: `204 No Content`
   - Errors: 404 (ChangeNotFoundError), 422 (ChangeNotUnlinkableError)

3. Modify `_get_detail()` helper to accept optional `asset_repo` and pass to query handler

4. Update `get_change_request` endpoint to inject `asset_repo = Depends(get_asset_repo)` and pass to `_get_detail()`

**Acceptance Criteria:**
- [x] `POST /{change_id}/assets` — links assets, 204 response
- [x] `DELETE /{change_id}/assets/{asset_id}` — unlinks asset, 204 response
- [x] Both endpoints use `db.commit()` after handler
- [x] `_get_detail()` accepts `asset_repo` parameter
- [x] `get_change_request` injects and passes `asset_repo`
- [x] Proper exception mapping (404, 422)

---

## Phase 5: Tests

### TASK-014: Unit tests for LinkAssetsCommand

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-008

**File:** `tests/unit/change_bc/change_request/application/commands/test_link_assets.py` (new)

**Test cases:**

1. **test_link_assets_success** — Links multiple assets, creates ChangeEvent with ASSET_LINKED
2. **test_link_assets_skips_duplicates** — Existing links are silently skipped
3. **test_link_assets_skips_invalid_assets** — Assets not found via asset_repo are silently skipped
4. **test_link_assets_terminal_state_raises** — Raises `InvalidStatusTransitionError` for terminal status
5. **test_link_assets_change_not_found_raises** — Raises `ChangeNotFoundError`
6. **test_link_assets_no_event_when_none_linked** — No ChangeEvent created if all skipped

**Acceptance Criteria:**
- [x] All 6 test cases implemented
- [x] Uses `MagicMock` for `change_repo` and `asset_repo`
- [x] Verifies `save_change_asset()` called for each valid link
- [x] Verifies `save_event()` called with correct event type and metadata
- [x] Verifies `save_event()` NOT called when linked count is 0

---

### TASK-015: Unit tests for UnlinkAssetCommand

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-009

**File:** `tests/unit/change_bc/change_request/application/commands/test_unlink_asset.py` (new)

**Test cases:**

1. **test_unlink_asset_success_draft** — Unlinks in DRAFT status
2. **test_unlink_asset_success_pending_approval** — Unlinks in PENDING_APPROVAL status
3. **test_unlink_asset_success_scheduled** — Unlinks in SCHEDULED status
4. **test_unlink_asset_in_progress_raises** — Raises `ChangeNotUnlinkableError` in IN_PROGRESS
5. **test_unlink_asset_implemented_raises** — Raises `ChangeNotUnlinkableError` in IMPLEMENTED
6. **test_unlink_asset_terminal_raises** — Raises `ChangeNotUnlinkableError` for terminal states
7. **test_unlink_asset_change_not_found_raises** — Raises `ChangeNotFoundError`

**Acceptance Criteria:**
- [x] All 7 test cases implemented
- [x] Uses `MagicMock` for `change_repo`
- [x] Verifies `delete_change_asset()` called with correct IDs
- [x] Verifies `save_event()` called with `ASSET_UNLINKED` event type
- [x] Tests all 3 allowed statuses and all disallowed statuses

---

### TASK-016: Integration tests for link/unlink endpoints

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-013

**File:** `tests/integration/test_change_request_endpoints.py` (modify)

**Test cases:**

1. **test_link_assets_success** — POST /changes/{id}/assets with valid asset_ids, verify 204
2. **test_link_assets_duplicates_skipped** — Link same asset twice, no error
3. **test_link_assets_terminal_state_rejected** — POST returns 422 for terminal state
4. **test_link_assets_change_not_found** — POST returns 404
5. **test_unlink_asset_success** — DELETE /changes/{id}/assets/{asset_id}, verify 204
6. **test_unlink_asset_status_guard** — DELETE returns 422 for IN_PROGRESS/IMPLEMENTED/terminal
7. **test_detail_includes_affected_assets** — GET /changes/{id} returns affected_assets array with asset details
8. **test_link_creates_change_event** — Verify ASSET_LINKED event in timeline after linking

**Acceptance Criteria:**
- [x] All 8 test cases implemented
- [x] Uses test fixtures from `tests/conftest.py`
- [x] Creates test assets in asset_bc for cross-BC validation
- [x] Verifies HTTP status codes (204, 404, 422)
- [x] Verifies affected_assets in detail response includes asset_name, asset_tag, brand, model
- [x] Verifies timeline includes ASSET_LINKED/ASSET_UNLINKED events

---

## Phase 6: Frontend

### TASK-017: Add affected assets section to ChangeDetailPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-013

**File:** `web/app/src/pages/admin/ChangeDetailPage.tsx` (modify)
**File:** `web/app/src/types/index.ts` (modify)

**Implementation:**

1. **Types** — Add `ChangeAsset` interface and extend `ChangeRequestDetail` with `affected_assets: ChangeAsset[]`

2. **Affected Assets section** on detail page:
   - Section header with count badge
   - Table: asset_name, asset_tag, brand/model, created_at, unlink button
   - "Link Assets" button opens modal to search and select assets (GET /api/v1/assets?search=)
   - Unlink button (trash icon) visible only in DRAFT/PENDING_APPROVAL/SCHEDULED
   - Link button visible in any non-terminal state
   - `useMutation` for POST /{id}/assets and DELETE /{id}/assets/{asset_id}
   - `queryClient.invalidateQueries(['change', id])` on success

**Acceptance Criteria:**
- [x] `ChangeAsset` TypeScript interface added
- [x] `ChangeRequestDetail` extended with `affected_assets`
- [x] Affected assets table displayed on detail page
- [x] Link assets modal with asset search
- [x] Unlink button with status guard (only DRAFT/PENDING_APPROVAL/SCHEDULED)
- [x] Link button with status guard (any non-terminal)
- [x] Mutations with cache invalidation
- [x] Empty state message when no assets linked

---

### TASK-018: Add i18n keys for asset linking

**Phase:** Frontend - i18n
**Complexity:** S
**Dependencies:** None

**Files:** `web/app/src/locales/en.ts` (modify), `web/app/src/locales/es.ts` (modify)

**Implementation:**

English keys:
```typescript
'page.change_detail.affected_assets': 'Affected Assets',
'page.change_detail.link_assets': 'Link Assets',
'page.change_detail.unlink_asset': 'Unlink',
'page.change_detail.no_assets_linked': 'No assets linked to this change',
'page.change_detail.search_assets': 'Search assets...',
'page.change_detail.link_assets_title': 'Link Assets to Change',
'toast.assets_linked': 'Assets linked successfully',
'toast.asset_unlinked': 'Asset unlinked successfully',
'enum.change_event.asset_linked': 'Assets Linked',
'enum.change_event.asset_unlinked': 'Asset Unlinked',
```

Spanish keys:
```typescript
'page.change_detail.affected_assets': 'Activos Afectados',
'page.change_detail.link_assets': 'Vincular Activos',
'page.change_detail.unlink_asset': 'Desvincular',
'page.change_detail.no_assets_linked': 'No hay activos vinculados a este cambio',
'page.change_detail.search_assets': 'Buscar activos...',
'page.change_detail.link_assets_title': 'Vincular Activos al Cambio',
'toast.assets_linked': 'Activos vinculados exitosamente',
'toast.asset_unlinked': 'Activo desvinculado exitosamente',
'enum.change_event.asset_linked': 'Activos Vinculados',
'enum.change_event.asset_unlinked': 'Activo Desvinculado',
```

**Acceptance Criteria:**
- [x] All 10 English keys added
- [x] All 10 Spanish keys added

---

## Dependency Graph

```
TASK-001 (enums) ──────────┐
TASK-002 (exceptions) ─────┤
TASK-003 (entity) ─────────┼──► TASK-004 (repo interface) ──► TASK-007 (repo impl)
                           │              │
TASK-005 (model) ──────────┘              │
TASK-006 (migration) ◄── TASK-005        │
                                          │
TASK-008 (link cmd) ◄── TASK-001, TASK-003, TASK-004
TASK-009 (unlink cmd) ◄── TASK-001, TASK-002, TASK-004
TASK-010 (detail query) ◄── TASK-003, TASK-004
TASK-011 (schemas) ── no deps
TASK-012 (dependencies) ── no deps
TASK-013 (router) ◄── TASK-008, TASK-009, TASK-010, TASK-011, TASK-012
TASK-014 (unit: link) ◄── TASK-008
TASK-015 (unit: unlink) ◄── TASK-009
TASK-016 (integration) ◄── TASK-013
TASK-017 (frontend) ◄── TASK-013
TASK-018 (i18n) ── no deps
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002, TASK-003, TASK-005, TASK-011, TASK-012, TASK-018
**Batch 2 (Parallel):** TASK-004, TASK-006
**Batch 3 (Parallel):** TASK-007, TASK-008, TASK-009, TASK-010
**Batch 4:** TASK-013
**Batch 5 (Parallel):** TASK-014, TASK-015, TASK-016, TASK-017

## Final Checklist

- [x] All 18 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] mypy passes (`make lint`)
- [x] TypeScript compiles (`npx tsc --noEmit` in web/app)
- [x] Migration applies cleanly
- [x] Affected assets visible on change detail page
- [x] Link/unlink works end-to-end
