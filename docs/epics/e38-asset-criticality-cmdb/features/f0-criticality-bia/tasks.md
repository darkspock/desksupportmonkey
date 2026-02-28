# Implementation Tasks: F0 — Criticality & BIA

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-26
**Total Tasks:** 17
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Enums | 1 | S |
| Domain — Entities | 1 | M |
| Infrastructure — Migrations | 1 | S |
| Infrastructure — Models | 1 | S |
| Infrastructure — Repositories | 1 | M |
| Application — Commands | 2 | S each |
| Application — Queries | 1 | S |
| HTTP — Schemas | 1 | S |
| HTTP — Router endpoints | 1 | M |
| Frontend — Types | 1 | S |
| Frontend — AssetDetailPage | 1 | M |
| Frontend — AssetListPage | 1 | M |
| Frontend — i18n | 1 | S |
| Tests — Unit | 1 | M |
| Tests — Integration | 1 | M |

---

## Phase 1: Domain Layer

### TASK-001: Add AssetCriticality enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add `AssetCriticality` enum to the existing enums file.

**File:** `src/asset_bc/asset/domain/enums.py`

**Implementation:**
```python
class AssetCriticality(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

**Acceptance Criteria:**
- [x] Enum with 4 values: CRITICAL, HIGH, MEDIUM, LOW
- [x] Inherits from `str, Enum` for JSON serialization
- [x] Added to existing `enums.py` file (not a new file)

---

### TASK-002: Extend Asset entity with criticality & BIA fields and methods

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Add 7 new nullable fields, 2 domain methods (`set_criticality()`, `update_bia()`), and `AssetDecommissionedError` exception to the existing Asset entity.

**File:** `src/asset_bc/asset/domain/entities.py`

**New fields on Asset dataclass:**
```python
criticality: Optional[AssetCriticality] = None
impact_score: Optional[int] = None
rto_minutes: Optional[int] = None
rpo_minutes: Optional[int] = None
bia_justification: Optional[str] = None
bia_reviewed_at: Optional[datetime] = None
bia_reviewed_by: Optional[str] = None
```

**New exception:**
```python
class AssetDecommissionedError(Exception):
    pass
```

**New methods:**
- `set_criticality(criticality: Optional[AssetCriticality]) -> dict` — Sets or clears criticality. Raises `AssetDecommissionedError` if asset is decommissioned. Returns change dict `{old, new}` for event recording, or empty dict if no change.
- `update_bia(impact_score, rto_minutes, rpo_minutes, justification, reviewed_by) -> dict` — Updates BIA fields. Validates: impact_score 1-10, rto_minutes > 0, rpo_minutes >= 0. Raises `AssetDecommissionedError` if decommissioned, `ValueError` for validation failures. Auto-sets `bia_reviewed_at` to `datetime.utcnow()` and `bia_reviewed_by`. Returns change dict.

**Acceptance Criteria:**
- [x] 7 new Optional fields with `None` defaults on Asset dataclass
- [x] `AssetDecommissionedError` exception class
- [x] `set_criticality()` raises `AssetDecommissionedError` on decommissioned assets
- [x] `set_criticality()` returns change dict or empty dict if no change
- [x] `set_criticality(None)` clears criticality
- [x] `update_bia()` validates impact_score range (1-10)
- [x] `update_bia()` validates rto_minutes > 0
- [x] `update_bia()` validates rpo_minutes >= 0
- [x] `update_bia()` auto-sets `bia_reviewed_at` and `bia_reviewed_by`
- [x] `update_bia()` raises `AssetDecommissionedError` on decommissioned assets
- [x] Import `AssetCriticality` from enums
- [x] Existing tests still pass (all new fields are Optional with None defaults)

---

## Phase 2: Infrastructure Layer

### TASK-003: Create Alembic migration for criticality & BIA columns

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Create Alembic migration adding 7 nullable columns to the `assets` table.

**File:** `alembic/versions/xxx_add_asset_criticality_bia_columns.py`

**Schema:**
```sql
ALTER TABLE assets ADD COLUMN criticality VARCHAR(20);
ALTER TABLE assets ADD COLUMN impact_score INTEGER;
ALTER TABLE assets ADD COLUMN rto_minutes INTEGER;
ALTER TABLE assets ADD COLUMN rpo_minutes INTEGER;
ALTER TABLE assets ADD COLUMN bia_justification TEXT;
ALTER TABLE assets ADD COLUMN bia_reviewed_at TIMESTAMP;
ALTER TABLE assets ADD COLUMN bia_reviewed_by VARCHAR(26) REFERENCES users(id);
CREATE INDEX ix_assets_criticality ON assets (criticality) WHERE criticality IS NOT NULL;
```

**Acceptance Criteria:**
- [x] 7 nullable columns added
- [x] `bia_reviewed_by` has FK to `users.id`
- [x] Partial index on `criticality` (WHERE NOT NULL)
- [x] Reversible (downgrade drops columns and index)
- [x] No default values (all nullable)

---

### TASK-004: Extend AssetModel with 7 new columns

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Add 7 new mapped columns to `AssetModel` using `Mapped[type]` annotations (SQLAlchemy 2.0 style).

**File:** `src/asset_bc/asset/infrastructure/models.py`

**New columns:**
```python
criticality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
impact_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
rto_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
rpo_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
bia_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
bia_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
bia_reviewed_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
```

**Acceptance Criteria:**
- [x] All 7 columns use `Mapped[Optional[type]]` annotations
- [x] `bia_reviewed_by` has `ForeignKey("users.id")`
- [x] All columns are `nullable=True`
- [x] Import `Text` added if not already imported

---

### TASK-005: Update AssetRepository to persist and hydrate new fields

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Update `AssetRepository.save()` to persist the 7 new fields in both update-existing and insert-new branches. Update entity hydration (model→entity conversion) to include new fields. Update `find_all()` to support `criticality` filter.

**File:** `src/asset_bc/asset/infrastructure/repository.py`

**Changes:**
1. **`save()` — update branch:** Add 7 new fields to the existing model update
2. **`save()` — insert branch:** Add 7 new fields to the new AssetModel constructor
3. **Entity hydration:** Ensure model→entity conversion includes new fields (criticality converted to `AssetCriticality` enum, others passed through)
4. **`find_all()`:** Add optional `criticality` parameter, add WHERE clause when provided

**Acceptance Criteria:**
- [x] `save()` persists all 7 new fields in update branch
- [x] `save()` persists all 7 new fields in insert branch
- [x] Entity hydration converts `criticality` string to `AssetCriticality` enum (or None)
- [x] Entity hydration includes all 7 new fields
- [x] `find_all()` accepts optional `criticality` filter parameter
- [x] `find_all()` filters by criticality when parameter is provided

---

## Phase 3: Application Layer

### TASK-006: Create SetCriticalityCommand + handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-005

**Description:**
Create `SetCriticalityCommand` and `SetCriticalityCommandHandler` following the existing `UpdateAssetCommand` pattern. Command + Handler in the same file.

**File:** `src/asset_bc/asset/application/commands/set_criticality.py`

**Command:**
```python
@dataclass
class SetCriticalityCommand(Command):
    asset_id: str
    company_id: str
    criticality: Optional[str]  # None to clear
    performed_by: str
```

**Handler logic:**
1. `find_by_id(asset_id, company_id)` → raise `AssetNotFoundError` if None
2. Convert `criticality` string to `AssetCriticality` enum (or None)
3. Call `asset.set_criticality(...)` — returns changes dict
4. `save(asset)`
5. If changes → `save_event(AssetEvent.create(asset_id, "criticality_set", changes, performed_by))`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler[SetCriticalityCommand]`
- [x] `handle()` returns `None`
- [x] `AssetNotFoundError` defined in same file
- [x] Records `criticality_set` AssetEvent with old/new values
- [x] Handles `None` criticality (clear)

---

### TASK-007: Create UpdateBiaCommand + handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-005

**Description:**
Create `UpdateBiaCommand` and `UpdateBiaCommandHandler` following the same pattern. Command + Handler in the same file.

**File:** `src/asset_bc/asset/application/commands/update_bia.py`

**Command:**
```python
@dataclass
class UpdateBiaCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    impact_score: Optional[int] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    bia_justification: Optional[str] = None
```

**Handler logic:**
1. `find_by_id(asset_id, company_id)` → raise `AssetNotFoundError` if None
2. Call `asset.update_bia(...)` with `reviewed_by=command.performed_by` — returns changes dict
3. `save(asset)`
4. If changes → `save_event(AssetEvent.create(asset_id, "bia_updated", changes, performed_by))`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler[UpdateBiaCommand]`
- [x] `handle()` returns `None`
- [x] `AssetNotFoundError` defined in same file
- [x] Records `bia_updated` AssetEvent with BIA field values
- [x] Passes `reviewed_by=command.performed_by` to entity method

---

### TASK-008: Add criticality filter to ListAssetsQuery

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Add `criticality` optional parameter to `ListAssetsQuery` dataclass and pass it through to the repository's `find_all()`.

**File:** `src/asset_bc/asset/application/queries/list_assets.py`

**Changes:**
- Add `criticality: Optional[str] = None` field to `ListAssetsQuery`
- Pass `criticality=query.criticality` in handler's call to `find_all()`

**Acceptance Criteria:**
- [x] `ListAssetsQuery` has new `criticality` field (Optional[str], default None)
- [x] Handler passes `criticality` to repository `find_all()`

---

## Phase 4: HTTP Layer

### TASK-009: Add request schemas and update AssetResponse

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-006, TASK-007

**Description:**
Add `SetCriticalityRequest` and `UpdateBiaRequest` Pydantic schemas. Add 7 new optional fields to `AssetResponse`.

**File:** `adapters/http/api/assets/schemas.py`

**New schemas:**
```python
class SetCriticalityRequest(BaseModel):
    criticality: Optional[str] = None

class UpdateBiaRequest(BaseModel):
    impact_score: Optional[int] = Field(None, ge=1, le=10)
    rto_minutes: Optional[int] = Field(None, gt=0)
    rpo_minutes: Optional[int] = Field(None, ge=0)
    bia_justification: Optional[str] = None
```

**AssetResponse additions:**
```python
criticality: Optional[str] = None
impact_score: Optional[int] = None
rto_minutes: Optional[int] = None
rpo_minutes: Optional[int] = None
bia_justification: Optional[str] = None
bia_reviewed_at: Optional[datetime] = None
bia_reviewed_by: Optional[str] = None
```

**Acceptance Criteria:**
- [x] `SetCriticalityRequest` allows `None` (to clear)
- [x] `UpdateBiaRequest` validates impact_score 1-10, rto_minutes > 0, rpo_minutes >= 0
- [x] `AssetResponse` includes all 7 new Optional fields

---

### TASK-010: Add PATCH endpoints and update router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-006, TASK-007, TASK-008, TASK-009

**Description:**
Add 2 new PATCH endpoints to the assets router. Update `_to_response()` helper to include new fields. Add `criticality` query parameter to `list_assets` endpoint.

**File:** `adapters/http/api/assets/routers.py`

**New endpoints:**
1. `PATCH /api/v1/assets/{asset_id}/criticality` — technician+ role, calls `SetCriticalityCommandHandler`
2. `PATCH /api/v1/assets/{asset_id}/bia` — technician+ role, calls `UpdateBiaCommandHandler`

**Error mapping (both endpoints):**
| Exception | HTTP Status |
|-----------|-------------|
| `AssetNotFoundError` | 404 |
| `AssetDecommissionedError` | 422 |
| `ValueError` | 422 |

**Collateral changes:**
- `_to_response()`: Add 7 new fields from asset entity (criticality as `.value` if not None)
- `list_assets()`: Add `criticality: Optional[str] = Query(None)` parameter, pass to `ListAssetsQuery`

**Acceptance Criteria:**
- [x] PATCH `/api/v1/assets/{id}/criticality` sets/clears criticality
- [x] PATCH `/api/v1/assets/{id}/bia` updates BIA fields
- [x] Both endpoints require technician+ role
- [x] Both endpoints catch `AssetNotFoundError` → 404
- [x] Both endpoints catch `AssetDecommissionedError` → 422
- [x] Both endpoints catch `ValueError` → 422
- [x] Both endpoints return updated asset via `_fetch_asset_response()`
- [x] `_to_response()` includes all 7 new fields
- [x] `list_assets` accepts `criticality` query parameter
- [x] Import new command handlers, schemas, and `AssetDecommissionedError`

---

## Phase 5: Frontend

### TASK-011: Update TypeScript Asset type

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Add 7 new fields to the `Asset` interface and add `AssetCriticality` type alias.

**File:** `web/app/src/types/index.ts`

**Changes to Asset interface:**
```typescript
criticality: string | null;
impact_score: number | null;
rto_minutes: number | null;
rpo_minutes: number | null;
bia_justification: string | null;
bia_reviewed_at: string | null;
bia_reviewed_by: string | null;
```

**New type:**
```typescript
export type AssetCriticality = 'critical' | 'high' | 'medium' | 'low';
```

**Acceptance Criteria:**
- [x] Asset interface has 7 new nullable fields
- [x] `AssetCriticality` type exported
- [x] TypeScript compiles clean (`npx tsc --noEmit`)

---

### TASK-012: Add criticality badge and BIA section to AssetDetailPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-011

**Description:**
Add criticality badge next to asset info, a criticality dropdown to set/change it, and a collapsible BIA section on the asset detail page.

**File:** `web/app/src/pages/technician/AssetDetailPage.tsx`

**Criticality badge:**
- Color-coded: red=critical, orange=high, yellow=medium, green=low, gray=unclassified
- Dropdown to set/change criticality (PATCH to `/api/v1/assets/{id}/criticality`)
- Invalidates asset query on success

**BIA section (collapsible panel):**
- Impact Score: number input (1-10)
- RTO: number input (minutes), display human-readable (e.g. "4 hours")
- RPO: number input (minutes), display human-readable
- Justification: textarea
- Last Reviewed: read-only display (auto-set on save)
- Save BIA button → PATCH to `/api/v1/assets/{id}/bia`
- Invalidates asset query on success

**Acceptance Criteria:**
- [x] Criticality badge displayed with correct colors
- [x] Criticality dropdown allows setting/clearing criticality
- [x] BIA section is collapsible
- [x] BIA fields: impact_score, rto_minutes, rpo_minutes, justification
- [x] Minutes displayed as human-readable (hours/minutes)
- [x] Last reviewed date shown as read-only
- [x] Save BIA calls PATCH endpoint
- [x] Both mutations invalidate and refetch asset data
- [x] Uses i18n keys for all labels

---

### TASK-013: Add criticality column and filter to AssetListPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-011

**Description:**
Add a criticality column to the asset list table and a criticality filter dropdown to the filters bar.

**File:** `web/app/src/pages/technician/AssetListPage.tsx`

**Criticality column:**
- Shows color-coded badge (same colors as detail page)
- Positioned after status column

**Criticality filter:**
- Dropdown in filters bar: All, Critical, High, Medium, Low, Unclassified
- Sends `criticality` query parameter to API

**Acceptance Criteria:**
- [x] Criticality column with color-coded badge in table
- [x] Criticality filter dropdown in filters bar
- [x] Filter sends `criticality` query param to list endpoint
- [x] "Unclassified" option filters for null criticality
- [x] Uses i18n keys for filter labels and badge text

---

### TASK-014: Add i18n EN/ES translations

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add i18n keys for criticality levels and BIA labels to both English and Spanish locale files.

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys (~15):**
- `asset.criticality` / `asset.criticality_critical` / `asset.criticality_high` / `asset.criticality_medium` / `asset.criticality_low` / `asset.criticality_unclassified`
- `asset.set_criticality`
- `asset.bia_section` / `asset.impact_score` / `asset.rto` / `asset.rpo` / `asset.bia_justification` / `asset.bia_last_reviewed` / `asset.save_bia`
- `asset.decommissioned_error`

**Acceptance Criteria:**
- [x] EN keys with English values
- [x] ES keys with Spanish translations
- [x] All labels used in TASK-012 and TASK-013 have corresponding i18n keys

---

## Phase 6: Tests

### TASK-015: Unit tests — domain methods and command handlers

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-006, TASK-007

**Description:**
Unit tests for the new domain methods and both command handlers.

**Files:**
- `tests/unit/asset_bc/asset/domain/test_entities.py` — extend with criticality/BIA tests
- `tests/unit/asset_bc/asset/application/commands/test_set_criticality.py` — NEW
- `tests/unit/asset_bc/asset/application/commands/test_update_bia.py` — NEW

**Domain entity tests (add to existing test file):**
- `set_criticality()` — set to each level, clear to None, verify change dict
- `set_criticality()` on decommissioned asset → raises `AssetDecommissionedError`
- `set_criticality()` same value → returns empty dict
- `update_bia()` — valid values, verify all fields set, verify reviewed_at/reviewed_by set
- `update_bia()` — impact_score out of range → ValueError
- `update_bia()` — rto_minutes <= 0 → ValueError
- `update_bia()` — rpo_minutes < 0 → ValueError
- `update_bia()` on decommissioned asset → raises `AssetDecommissionedError`

**SetCriticalityCommandHandler tests:**
- Happy path: set criticality, verify save + event
- Clear criticality (None): verify save + event
- Asset not found → `AssetNotFoundError`
- Decommissioned → `AssetDecommissionedError` propagated

**UpdateBiaCommandHandler tests:**
- Happy path: set BIA fields, verify save + event
- Asset not found → `AssetNotFoundError`
- Invalid impact_score → `ValueError` propagated
- Decommissioned → `AssetDecommissionedError` propagated

**Acceptance Criteria:**
- [x] All entity domain method test cases listed above
- [x] All command handler test cases listed above
- [x] Handlers use `MagicMock` for repository
- [x] All tests pass (`make test`)

---

### TASK-016: Integration tests — PATCH endpoints

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-010

**Description:**
Integration tests for the two new PATCH endpoints and the criticality filter on list.

**File:** `tests/integration/test_asset_endpoints.py` (extend existing)

**Test cases:**
- PATCH `/assets/{id}/criticality` — set criticality → 200, verify response has criticality
- PATCH `/assets/{id}/criticality` — clear to null → 200, verify response has null criticality
- PATCH `/assets/{id}/criticality` — asset not found → 404
- PATCH `/assets/{id}/criticality` — decommissioned asset → 422
- PATCH `/assets/{id}/bia` — set BIA fields → 200, verify response
- PATCH `/assets/{id}/bia` — invalid impact_score → 422
- PATCH `/assets/{id}/bia` — invalid rto_minutes → 422
- PATCH `/assets/{id}/bia` — asset not found → 404
- GET `/assets` with `criticality=critical` → returns only critical assets
- GET `/assets/{id}` → response includes new fields (null by default)
- Verify AssetEvent recorded for criticality_set
- Verify AssetEvent recorded for bia_updated

**Acceptance Criteria:**
- [x] All test cases listed above
- [x] Uses TestClient + real PostgreSQL
- [x] Tests pass (`make test-integration`)

---

### TASK-017: Verify TypeScript and run all tests

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Final verification that everything compiles and all test suites pass.

**Commands:**
```bash
npx tsc --noEmit        # TypeScript clean
make test                # Unit tests pass
make test-integration    # Integration tests pass
```

**Acceptance Criteria:**
- [x] TypeScript compiles with no errors
- [x] All unit tests pass
- [x] All integration tests pass
- [x] No regressions in existing tests

---

## Dependency Graph

```
TASK-001 (Enum)
    │
    └── TASK-002 (Entity extension)
            │
            ├── TASK-003 (Migration)
            │       │
            │       └── TASK-004 (Model)
            │               │
            │               └── TASK-005 (Repository)
            │                       │
            │                       ├── TASK-006 (SetCriticalityCommand)
            │                       │       │
            │                       │       ├── TASK-009 (Schemas)
            │                       │       │       │
            │                       │       │       └── TASK-010 (Router)──── TASK-016 (Integration tests)
            │                       │       │
            │                       │       └── TASK-015 (Unit tests)
            │                       │
            │                       ├── TASK-007 (UpdateBiaCommand)
            │                       │       │
            │                       │       ├── TASK-009 (Schemas)
            │                       │       │
            │                       │       └── TASK-015 (Unit tests)
            │                       │
            │                       └── TASK-008 (ListAssetsQuery filter)
            │                               │
            │                               └── TASK-010 (Router)
            │
            └── TASK-011 (TS types)
                    │
                    ├── TASK-012 (AssetDetailPage)
                    │
                    └── TASK-013 (AssetListPage)

TASK-014 (i18n) ── no dependencies, can run anytime

TASK-017 (Verification) ── depends on ALL
```

## Execution Order

**Batch 1:** TASK-001, TASK-014
**Batch 2:** TASK-002
**Batch 3:** TASK-003
**Batch 4:** TASK-004, TASK-011
**Batch 5:** TASK-005
**Batch 6:** TASK-006, TASK-007, TASK-008
**Batch 7:** TASK-009
**Batch 8:** TASK-010, TASK-012, TASK-013, TASK-015
**Batch 9:** TASK-016
**Batch 10:** TASK-017

## Final Checklist

- [x] All 17 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] TypeScript compiles clean (`npx tsc --noEmit`)
- [x] No regressions in existing tests
- [x] All acceptance criteria from requirements.md met
