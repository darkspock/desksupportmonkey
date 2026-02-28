# Implementation Tasks: Impact Propagation & CMDB Dashboard

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-26
**Total Tasks:** 18
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Repository Interfaces | 2 | S |
| Infrastructure - Repositories | 2 | M |
| Application - Queries | 2 | M-L |
| HTTP - Schemas | 1 | S |
| HTTP - Endpoints | 1 | M |
| Tests - Unit | 2 | M |
| Tests - Integration | 2 | M |
| Frontend - Types | 1 | S |
| Frontend - Pages | 2 | M-L |
| Frontend - Navigation & i18n | 3 | S |

---

## Phase 1: Domain Layer - Repository Interfaces

### TASK-001: Extend AssetRepositoryInterface with 4 new abstract methods

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add 4 new abstract methods to the existing `AssetRepositoryInterface` for CMDB dashboard aggregation queries.

**File:** `src/asset_bc/asset/domain/repository.py`

**Methods to add:**

```python
@abstractmethod
def count_by_criticality(self, company_id: str) -> dict[str, int]: ...

@abstractmethod
def bia_coverage_stats(self, company_id: str) -> dict: ...

@abstractmethod
def count_orphan_critical_assets(self, company_id: str) -> int: ...

@abstractmethod
def find_overdue_bia_reviews(self, company_id: str, months: int) -> list[dict]: ...
```

**Acceptance Criteria:**
- [x] `count_by_criticality` — abstract method with `(company_id: str) -> dict[str, int]` signature
- [x] `bia_coverage_stats` — abstract method with `(company_id: str) -> dict` signature
- [x] `count_orphan_critical_assets` — abstract method with `(company_id: str) -> int` signature
- [x] `find_overdue_bia_reviews` — abstract method with `(company_id: str, months: int) -> list[dict]` signature
- [x] All methods decorated with `@abstractmethod`

---

### TASK-002: Extend CIRelationshipRepositoryInterface with 4 new abstract methods

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add 4 new abstract methods to the existing `CIRelationshipRepositoryInterface` for BFS traversal and dashboard aggregation.

**File:** `src/asset_bc/asset/domain/repository.py`

**Methods to add:**

```python
@abstractmethod
def find_all_by_company(self, company_id: str) -> list[CIRelationship]: ...

@abstractmethod
def count_all(self, company_id: str) -> int: ...

@abstractmethod
def count_by_type(self, company_id: str) -> dict[str, int]: ...

@abstractmethod
def count_incoming_by_asset(self, company_id: str, limit: int = 10) -> list[dict]: ...
```

**Acceptance Criteria:**
- [x] `find_all_by_company` — abstract method returning `list[CIRelationship]`
- [x] `count_all` — abstract method returning `int`
- [x] `count_by_type` — abstract method returning `dict[str, int]`
- [x] `count_incoming_by_asset` — abstract method returning `list[dict]` with `limit` param defaulting to 10
- [x] All methods decorated with `@abstractmethod`

---

## Phase 2: Infrastructure Layer - Repositories

### TASK-003: Implement 4 new AssetRepository methods

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Implement the 4 new abstract methods in `AssetRepository` using SQLAlchemy queries.

**File:** `src/asset_bc/asset/infrastructure/repository.py`

**Implementations:**

| Method | SQL Pattern |
|--------|-------------|
| `count_by_criticality` | `SELECT COALESCE(criticality, 'unclassified'), COUNT(*) FROM assets WHERE company_id = ? AND status != 'disposed' GROUP BY 1` |
| `bia_coverage_stats` | `SELECT COUNT(*) FILTER (WHERE criticality IN ('critical','high')) as total, COUNT(*) FILTER (WHERE criticality IN ('critical','high') AND impact_score IS NOT NULL AND rto_minutes IS NOT NULL) as has_bia FROM assets WHERE company_id = ? AND status != 'disposed'` |
| `count_orphan_critical_assets` | `SELECT COUNT(*) FROM assets a WHERE a.company_id = ? AND a.criticality = 'critical' AND a.status != 'disposed' AND NOT EXISTS (SELECT 1 FROM ci_relationships cr WHERE cr.company_id = ? AND (cr.source_asset_id = a.id OR cr.target_asset_id = a.id))` |
| `find_overdue_bia_reviews` | `SELECT id, name, asset_tag, criticality, bia_reviewed_at FROM assets WHERE company_id = ? AND criticality IN ('critical','high') AND status != 'disposed' AND (bia_reviewed_at IS NULL OR bia_reviewed_at < now() - interval '{months} months') ORDER BY criticality, name` |

**Acceptance Criteria:**
- [x] `count_by_criticality` groups by criticality, maps NULL to `"unclassified"`, excludes disposed
- [x] `bia_coverage_stats` returns dict with `total_critical_high`, `has_bia`, `coverage_pct` (float, 0.0 if no critical/high)
- [x] `count_orphan_critical_assets` uses NOT EXISTS subquery against `ci_relationships`, excludes disposed
- [x] `find_overdue_bia_reviews` returns list of dicts with `id`, `name`, `asset_tag`, `criticality`, `bia_reviewed_at`; includes both NULL and old dates; ordered by criticality, name
- [x] All methods use SQLAlchemy ORM/Core queries (not raw SQL strings)

---

### TASK-004: Implement 4 new CIRelationshipRepository methods

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002

**Description:**
Implement the 4 new abstract methods in `CIRelationshipRepository` using SQLAlchemy queries.

**File:** `src/asset_bc/asset/infrastructure/ci_relationship_repository.py`

**Implementations:**

| Method | SQL Pattern |
|--------|-------------|
| `find_all_by_company` | `SELECT * FROM ci_relationships WHERE company_id = ?` |
| `count_all` | `SELECT COUNT(*) FROM ci_relationships WHERE company_id = ?` |
| `count_by_type` | `SELECT relationship_type, COUNT(*) FROM ci_relationships WHERE company_id = ? GROUP BY 1` |
| `count_incoming_by_asset` | `SELECT cr.target_asset_id, a.name, a.asset_tag, COUNT(*) as cnt FROM ci_relationships cr JOIN assets a ON cr.target_asset_id = a.id WHERE cr.company_id = ? GROUP BY 1,2,3 ORDER BY cnt DESC LIMIT ?` |

**Acceptance Criteria:**
- [x] `find_all_by_company` returns all relationships as domain entities, filtered by `company_id`
- [x] `count_all` returns integer count
- [x] `count_by_type` returns dict mapping relationship type string to count
- [x] `count_incoming_by_asset` joins `assets` table, returns list of dicts with `asset_id`, `asset_name`, `asset_tag`, `count`, ordered desc by count, limited to `limit` param
- [x] All methods use SQLAlchemy ORM/Core queries

---

## Phase 3: Application Layer - Queries

### TASK-005: Create GetAssetImpactQuery + Handler with BFS traversal

**Phase:** Application
**Complexity:** L
**Dependencies:** TASK-001, TASK-002

**Description:**
Create the impact propagation query handler implementing iterative BFS for upstream/downstream traversal with cycle detection and impact radius calculation.

**File:** `src/asset_bc/asset/application/queries/get_asset_impact.py`

**DTOs:**

```python
@dataclass
class ImpactAssetDto:
    id: str
    name: str
    asset_tag: Optional[str]
    criticality: Optional[str]
    depth: int
    relationship_type: str

@dataclass
class ImpactRadiusDto:
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unclassified: int = 0
    total: int = 0

@dataclass
class AssetImpactDto:
    asset_id: str
    upstream: list[ImpactAssetDto]
    downstream: list[ImpactAssetDto]
    radius: ImpactRadiusDto
```

**Query:**

```python
@dataclass
class GetAssetImpactQuery(Query):
    asset_id: str
    company_id: str
    max_depth: int = 5
```

**Handler:** `GetAssetImpactQueryHandler(QueryHandler[GetAssetImpactQuery, AssetImpactDto])`

**Dependencies:** `asset_repo: AssetRepositoryInterface`, `ci_repo: CIRelationshipRepositoryInterface`

**Algorithm:**
1. Validate asset exists via `asset_repo.find_by_id(asset_id, company_id)` → raise `AssetNotFoundError` if None
2. Load all relationships: `ci_repo.find_all_by_company(company_id)`
3. Build adjacency maps from relationships:
   - Map by `source_asset_id` → for upstream traversal (source depends on target)
   - Map by `target_asset_id` → for downstream traversal (source depends on target, so target is depended upon)
4. BFS upstream: from `asset_id`, follow relationships where `source_asset_id == current`, recurse into `target_asset_id`. Visited set prevents cycles. Track depth per node.
5. BFS downstream: from `asset_id`, follow relationships where `target_asset_id == current`, recurse into `source_asset_id`. Visited set prevents cycles. Track depth per node.
6. Load asset details: `asset_repo.find_by_ids(all_discovered_ids, company_id)`
7. Build `ImpactAssetDto` list for upstream and downstream
8. Compute `ImpactRadiusDto` from downstream assets grouped by criticality (None → "unclassified")
9. Return `AssetImpactDto`

**Acceptance Criteria:**
- [x] Inherits from `QueryHandler[GetAssetImpactQuery, AssetImpactDto]`
- [x] Validates asset exists, raises `AssetNotFoundError` if not found
- [x] Loads all company relationships in single call (no N+1)
- [x] BFS upstream traversal with visited set and max_depth limit
- [x] BFS downstream traversal with visited set and max_depth limit
- [x] Cycle detection: visited set prevents infinite loops
- [x] Correct direction semantics: upstream follows source→target, downstream follows target→source
- [x] Impact radius groups downstream assets by criticality, None mapped to "unclassified"
- [x] Each `ImpactAssetDto` includes correct `depth` and `relationship_type`

---

### TASK-006: Create GetCMDBDashboardQuery + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**Description:**
Create the CMDB dashboard aggregation query handler that assembles all dashboard metrics from repository calls.

**File:** `src/asset_bc/asset/application/queries/cmdb_dashboard.py`

**DTOs:**

```python
@dataclass
class MostDependedAssetDto:
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    incoming_count: int

@dataclass
class OverdueBIAReviewDto:
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    criticality: str
    bia_reviewed_at: Optional[datetime]

@dataclass
class CMDBDashboardDto:
    criticality_distribution: dict[str, int]
    orphan_critical_count: int
    bia_total_critical_high: int
    bia_has_coverage: int
    bia_coverage_pct: float
    total_relationships: int
    relationships_by_type: dict[str, int]
    most_depended_upon: list[MostDependedAssetDto]
    overdue_bia_reviews: list[OverdueBIAReviewDto]
```

**Query:**

```python
@dataclass
class GetCMDBDashboardQuery(Query):
    company_id: str
```

**Handler:** `GetCMDBDashboardQueryHandler(QueryHandler[GetCMDBDashboardQuery, CMDBDashboardDto])`

**Dependencies:** `asset_repo: AssetRepositoryInterface`, `ci_repo: CIRelationshipRepositoryInterface`

**Handler logic:**
1. `criticality_distribution = asset_repo.count_by_criticality(company_id)`
2. `orphan_critical_count = asset_repo.count_orphan_critical_assets(company_id)`
3. `bia_stats = asset_repo.bia_coverage_stats(company_id)`
4. `total_relationships = ci_repo.count_all(company_id)`
5. `relationships_by_type = ci_repo.count_by_type(company_id)`
6. `most_depended_raw = ci_repo.count_incoming_by_asset(company_id)`
7. `overdue_raw = asset_repo.find_overdue_bia_reviews(company_id, months=6)`
8. Assemble and return `CMDBDashboardDto`

**Acceptance Criteria:**
- [x] Inherits from `QueryHandler[GetCMDBDashboardQuery, CMDBDashboardDto]`
- [x] Calls all 7 repository methods and assembles DTO
- [x] Maps `most_depended_raw` dicts to `MostDependedAssetDto` list
- [x] Maps `overdue_raw` dicts to `OverdueBIAReviewDto` list
- [x] Extracts `bia_total_critical_high`, `bia_has_coverage`, `bia_coverage_pct` from `bia_stats` dict
- [x] No business logic — pure aggregation

---

## Phase 4: HTTP Layer

### TASK-007: Add response schemas for Impact and CMDB Dashboard

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-005, TASK-006

**Description:**
Add 6 new Pydantic response models to the assets schemas file.

**File:** `adapters/http/api/assets/schemas.py`

**Schemas to add:**

```python
class ImpactAssetResponse(BaseModel):
    id: str
    name: str
    asset_tag: Optional[str]
    criticality: Optional[str]
    depth: int
    relationship_type: str

class ImpactRadiusResponse(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    unclassified: int
    total: int

class AssetImpactResponse(BaseModel):
    asset_id: str
    upstream: list[ImpactAssetResponse]
    downstream: list[ImpactAssetResponse]
    radius: ImpactRadiusResponse

class MostDependedAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    incoming_count: int

class OverdueBIAReviewResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    criticality: str
    bia_reviewed_at: Optional[datetime]

class CMDBDashboardResponse(BaseModel):
    criticality_distribution: dict[str, int]
    orphan_critical_count: int
    bia_total_critical_high: int
    bia_has_coverage: int
    bia_coverage_pct: float
    total_relationships: int
    relationships_by_type: dict[str, int]
    most_depended_upon: list[MostDependedAssetResponse]
    overdue_bia_reviews: list[OverdueBIAReviewResponse]
```

**Acceptance Criteria:**
- [x] All 6 Pydantic models created with correct field types
- [x] `datetime` import added if not already present
- [x] Models follow existing schema naming conventions in the file

---

### TASK-008: Add GET /cmdb-dashboard and GET /{asset_id}/impact endpoints

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-005, TASK-006, TASK-007

**Description:**
Add two new endpoints to the assets router. **Critical:** `GET /cmdb-dashboard` must be placed BEFORE `GET /{asset_id}` to avoid route shadowing.

**File:** `adapters/http/api/assets/routers.py`

**Endpoint 1 — CMDB Dashboard:**

```python
@router.get("/cmdb-dashboard")
def get_cmdb_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    asset_repo=Depends(get_asset_repo),
    ci_repo=Depends(get_ci_relationship_repo),
):
    handler = GetCMDBDashboardQueryHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    dto = handler.handle(GetCMDBDashboardQuery(company_id=current_user.company_id))
    return {"data": CMDBDashboardResponse(
        criticality_distribution=dto.criticality_distribution,
        orphan_critical_count=dto.orphan_critical_count,
        bia_total_critical_high=dto.bia_total_critical_high,
        bia_has_coverage=dto.bia_has_coverage,
        bia_coverage_pct=dto.bia_coverage_pct,
        total_relationships=dto.total_relationships,
        relationships_by_type=dto.relationships_by_type,
        most_depended_upon=[
            MostDependedAssetResponse(
                asset_id=m.asset_id,
                asset_name=m.asset_name,
                asset_tag=m.asset_tag,
                incoming_count=m.incoming_count,
            ) for m in dto.most_depended_upon
        ],
        overdue_bia_reviews=[
            OverdueBIAReviewResponse(
                asset_id=o.asset_id,
                asset_name=o.asset_name,
                asset_tag=o.asset_tag,
                criticality=o.criticality,
                bia_reviewed_at=o.bia_reviewed_at,
            ) for o in dto.overdue_bia_reviews
        ],
    ).model_dump(mode="json")}
```

**Endpoint 2 — Asset Impact:**

```python
@router.get("/{asset_id}/impact")
def get_asset_impact(
    asset_id: str,
    max_depth: int = Query(default=5, ge=1, le=10),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo=Depends(get_asset_repo),
    ci_repo=Depends(get_ci_relationship_repo),
):
    handler = GetAssetImpactQueryHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    try:
        dto = handler.handle(GetAssetImpactQuery(
            asset_id=asset_id,
            company_id=current_user.company_id,
            max_depth=max_depth,
        ))
    except AssetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": AssetImpactResponse(
        asset_id=dto.asset_id,
        upstream=[ImpactAssetResponse(...) for a in dto.upstream],
        downstream=[ImpactAssetResponse(...) for a in dto.downstream],
        radius=ImpactRadiusResponse(
            critical=dto.radius.critical,
            high=dto.radius.high,
            medium=dto.radius.medium,
            low=dto.radius.low,
            unclassified=dto.radius.unclassified,
            total=dto.radius.total,
        ),
    ).model_dump(mode="json")}
```

**Acceptance Criteria:**
- [x] `GET /cmdb-dashboard` placed BEFORE `GET /{asset_id}` in the router (after `/locations` block)
- [x] `GET /cmdb-dashboard` requires ADMIN role
- [x] `GET /{asset_id}/impact` requires TECHNICIAN+ role
- [x] `max_depth` query param with default=5, ge=1, le=10
- [x] Impact endpoint catches `AssetNotFoundError` → 404
- [x] Both endpoints use existing `get_asset_repo` and `get_ci_relationship_repo` dependencies
- [x] All necessary imports added (query handlers, schemas, exceptions)

---

## Phase 5: Tests

### TASK-009: Unit tests for GetAssetImpactQueryHandler

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create unit tests for the BFS traversal query handler with mocked repositories.

**File:** `tests/unit/asset_bc/asset/application/queries/test_get_asset_impact.py`

**Test cases (from design):**

1. **No relationships** → empty upstream/downstream, zero radius
2. **Flat dependencies** (depth 1 only) → correct upstream/downstream separation
3. **Nested dependencies** (depth 2-3) → BFS traverses multiple levels, correct depth values
4. **Cycle detection** → A→B→C→A does not infinite loop, each node appears once
5. **Max depth limit** → relationships beyond max_depth are not included
6. **Mixed relationship types** → correct traversal regardless of type
7. **Asset not found** → raises `AssetNotFoundError`
8. **Impact radius calculation** → downstream assets correctly grouped by criticality, None → "unclassified"

**Acceptance Criteria:**
- [x] All 8 test cases implemented
- [x] Uses `MagicMock` for `AssetRepositoryInterface` and `CIRelationshipRepositoryInterface`
- [x] Tests cycle detection with circular relationship chain (A→B→C→A)
- [x] Tests depth tracking (nested traversal returns correct depth per node)
- [x] Tests max_depth enforcement
- [x] Tests direction semantics (upstream vs downstream correctly separated)
- [x] Tests radius grouping with None criticality → "unclassified"
- [x] Tests `AssetNotFoundError` raised when asset doesn't exist

---

### TASK-010: Unit tests for GetCMDBDashboardQueryHandler

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-006

**Description:**
Create unit tests for the dashboard aggregation query handler with mocked repositories.

**File:** `tests/unit/asset_bc/asset/application/queries/test_cmdb_dashboard.py`

**Test cases (from design):**

1. **All metrics populated** → correct DTO assembly from repo data
2. **Empty company** → zero counts, empty lists, 0.0 coverage_pct
3. **Orphan calculation** → critical asset with no relationships counted
4. **BIA coverage** → percentage computed correctly (has_bia / total_critical_high * 100)
5. **Overdue BIA reviews** → null and old dates both included in result

**Acceptance Criteria:**
- [x] All 5 test cases implemented
- [x] Uses `MagicMock` for both repositories
- [x] Tests correct mapping of raw dicts to `MostDependedAssetDto` list
- [x] Tests correct mapping of raw dicts to `OverdueBIAReviewDto` list
- [x] Tests edge case: zero critical/high assets → coverage_pct = 0.0 (no division by zero)
- [x] Tests all 7 repository method calls are made

---

### TASK-011: Integration tests for GET /assets/{id}/impact endpoint

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Create integration tests for the asset impact endpoint using real database.

**File:** `tests/integration/test_asset_impact_endpoints.py`

**Test cases:**

1. **Auth guard** — unauthenticated request → 401
2. **Asset not found** — nonexistent asset_id → 404
3. **Empty relationships** — valid asset, no relationships → 200 with empty upstream/downstream
4. **With relationships** — seed assets + CI relationships → 200 with correct upstream/downstream/radius
5. **Cycle handling** — seed circular relationships → 200 without infinite loop

**Acceptance Criteria:**
- [x] Uses `client` and `auth_as` fixtures from `tests/conftest.py`
- [x] Seeds test assets and CI relationships in the database
- [x] Tests correct HTTP status codes (401, 404, 200)
- [x] Verifies response structure matches `AssetImpactResponse` schema
- [x] Verifies impact radius values in response

---

### TASK-012: Integration tests for GET /assets/cmdb-dashboard endpoint

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Create integration tests for the CMDB dashboard endpoint using real database.

**File:** `tests/integration/test_cmdb_dashboard_endpoints.py`

**Test cases:**

1. **Auth guard** — unauthenticated request → 401
2. **Role guard** — technician request → 403 (admin only)
3. **Empty company** — no assets → 200 with zero counts
4. **Populated dashboard** — seed assets with various criticalities + CI relationships → 200 with correct stats

**Acceptance Criteria:**
- [x] Uses `client` and `auth_as` fixtures from `tests/conftest.py`
- [x] Tests correct HTTP status codes (401, 403, 200)
- [x] Verifies response structure matches `CMDBDashboardResponse` schema
- [x] Admin-only access enforced

---

## Phase 6: Frontend

### TASK-013: Add TypeScript interfaces for Impact and CMDB Dashboard

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-007

**Description:**
Add TypeScript interfaces matching the backend response schemas.

**File:** `web/app/src/types/index.ts`

**Interfaces to add:**

```typescript
export interface ImpactAsset {
  id: string;
  name: string;
  asset_tag: string | null;
  criticality: string | null;
  depth: number;
  relationship_type: string;
}

export interface ImpactRadius {
  critical: number;
  high: number;
  medium: number;
  low: number;
  unclassified: number;
  total: number;
}

export interface AssetImpact {
  asset_id: string;
  upstream: ImpactAsset[];
  downstream: ImpactAsset[];
  radius: ImpactRadius;
}

export interface MostDependedAsset {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  incoming_count: number;
}

export interface OverdueBIAReview {
  asset_id: string;
  asset_name: string;
  asset_tag: string | null;
  criticality: string;
  bia_reviewed_at: string | null;
}

export interface CMDBDashboard {
  criticality_distribution: Record<string, number>;
  orphan_critical_count: number;
  bia_total_critical_high: number;
  bia_has_coverage: number;
  bia_coverage_pct: number;
  total_relationships: number;
  relationships_by_type: Record<string, number>;
  most_depended_upon: MostDependedAsset[];
  overdue_bia_reviews: OverdueBIAReview[];
}
```

**Acceptance Criteria:**
- [x] All interfaces match backend response schemas exactly
- [x] Exported from `types/index.ts`

---

### TASK-014: Create CMDBDashboardPage

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-013

**Description:**
Create the CMDB dashboard page following the `SupplyChainDashboardPage.tsx` pattern exactly.

**File:** `web/app/src/pages/admin/CMDBDashboardPage.tsx`

**Pattern:** Follow `SupplyChainDashboardPage.tsx` — single `useQuery`, local helper components, pure CSS bars, Tailwind styling.

**Sections:**
1. **Stat cards row** (grid 2x4): criticality counts summary, Orphan Critical Assets count, BIA Coverage %, Total CI Relationships
2. **Criticality Distribution** — horizontal bar chart (pure CSS, like RiskBar): critical/high/medium/low/unclassified
3. **CI Relationships by Type** — horizontal bar chart: runs_on/depends_on/connected_to/part_of/backs_up
4. **Most Depended-Upon Assets** table (top 10): Asset Name, Asset Tag, Incoming Count
5. **Overdue BIA Reviews** table: Asset Name, Asset Tag, Criticality, Last Reviewed

**Data fetch:** `useQuery` to `GET /api/v1/assets/cmdb-dashboard`

**Acceptance Criteria:**
- [x] Single `useQuery` for data fetching
- [x] Loading state with `Loading` component
- [x] Error state with `ErrorState` component
- [x] Stat cards grid with 4 summary cards
- [x] Criticality distribution bar chart (pure CSS)
- [x] Relationships by type bar chart (pure CSS)
- [x] Most depended-upon assets table (or empty state message)
- [x] Overdue BIA reviews table (or empty state message)
- [x] All text uses `useI18n()` for translations
- [x] Tailwind styling: `max-w-7xl mx-auto space-y-6`, grid layout

---

### TASK-015: Enhance AssetDetailPage Dependencies tab with impact radius

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-013

**Description:**
Add impact radius summary at the top of the Dependencies tab section in AssetDetailPage, above the existing "Depends On" / "Depended On By" tables.

**File:** `web/app/src/pages/technician/AssetDetailPage.tsx`

**Data fetch:** `useQuery` to `GET /api/v1/assets/${id}/impact`

**UI:** Row of color-coded badge/pill elements:
```
Impact Radius: [Critical: 3] [High: 5] [Medium: 2] [Low: 1] [Total: 11]
```
- critical=red, high=orange, medium=yellow, low=green
- Only shown when downstream total > 0

**Acceptance Criteria:**
- [x] `useQuery` fetches impact data from `GET /api/v1/assets/${id}/impact`
- [x] Impact radius badges displayed above "Depends On" / "Depended On By" tables
- [x] Color-coded by criticality: critical=red, high=orange, medium=yellow, low=green
- [x] Only shown when `radius.total > 0`
- [x] Uses `useI18n()` for labels
- [x] Does not break existing Dependencies tab layout

---

### TASK-016: Add CMDB Dashboard route, navSections entry, and Sidebar icon

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-014

**Description:**
Wire up the CMDB Dashboard page in the router, navigation sections, and sidebar icon.

**Files:**
- `web/app/src/router.tsx` — add lazy import + route
- `web/app/src/config/navSections.ts` — add nav entry under Operations section
- `web/app/src/components/layout/Sidebar.tsx` — add icon mapping

**router.tsx changes:**

```tsx
const CMDBDashboardPage = lazy(() => import('./pages/admin/CMDBDashboardPage'));
// Under admin routes:
{ path: 'cmdb/dashboard', element: <RequireRole roles={['admin', 'super_admin']}><S><CMDBDashboardPage /></S></RequireRole> }
```

**navSections.ts changes:**

```ts
{ to: '/cmdb/dashboard', labelKey: 'nav.cmdb_dashboard', roles: ['admin', 'super_admin'] },
```

**Sidebar.tsx changes:** Add icon mapping for `/cmdb/dashboard` (network/topology SVG icon).

**Acceptance Criteria:**
- [x] Lazy import added in router.tsx
- [x] Route `/cmdb/dashboard` added with admin/super_admin guard
- [x] Nav entry added under Operations section in navSections.ts
- [x] Icon mapping added in Sidebar.tsx for `/cmdb/dashboard`

---

### TASK-017: Add i18n translations (EN)

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add English i18n keys for CMDB dashboard and impact radius labels.

**File:** `web/app/src/locales/en.ts`

**Keys to add:**

```
nav.cmdb_dashboard: "CMDB Dashboard"
page.cmdb_dashboard.title: "CMDB Dashboard"
page.cmdb_dashboard.criticality_distribution: "Criticality Distribution"
page.cmdb_dashboard.orphan_critical: "Orphan Critical Assets"
page.cmdb_dashboard.bia_coverage: "BIA Coverage"
page.cmdb_dashboard.total_relationships: "Total Relationships"
page.cmdb_dashboard.relationships_by_type: "Relationships by Type"
page.cmdb_dashboard.most_depended: "Most Depended-Upon Assets"
page.cmdb_dashboard.overdue_bia: "Overdue BIA Reviews"
page.cmdb_dashboard.asset_name: "Asset Name"
page.cmdb_dashboard.asset_tag: "Asset Tag"
page.cmdb_dashboard.incoming_count: "Dependencies"
page.cmdb_dashboard.last_reviewed: "Last Reviewed"
page.cmdb_dashboard.never: "Never"
page.cmdb_dashboard.no_overdue: "All BIA reviews are up to date"
page.cmdb_dashboard.no_most_depended: "No dependency relationships found"
page.asset_detail.impact_radius: "Impact Radius"
page.asset_detail.impact_total: "Total"
```

**Acceptance Criteria:**
- [x] All 17 i18n keys added
- [x] Keys follow existing naming convention

---

### TASK-018: Add i18n translations (ES)

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add Spanish i18n keys for CMDB dashboard and impact radius labels.

**File:** `web/app/src/locales/es.ts`

**Keys to add (Spanish translations of TASK-017):**

```
nav.cmdb_dashboard: "Panel CMDB"
page.cmdb_dashboard.title: "Panel CMDB"
page.cmdb_dashboard.criticality_distribution: "Distribución de Criticidad"
page.cmdb_dashboard.orphan_critical: "Activos Críticos Huérfanos"
page.cmdb_dashboard.bia_coverage: "Cobertura BIA"
page.cmdb_dashboard.total_relationships: "Relaciones Totales"
page.cmdb_dashboard.relationships_by_type: "Relaciones por Tipo"
page.cmdb_dashboard.most_depended: "Activos Más Dependidos"
page.cmdb_dashboard.overdue_bia: "Revisiones BIA Vencidas"
page.cmdb_dashboard.asset_name: "Nombre del Activo"
page.cmdb_dashboard.asset_tag: "Etiqueta"
page.cmdb_dashboard.incoming_count: "Dependencias"
page.cmdb_dashboard.last_reviewed: "Última Revisión"
page.cmdb_dashboard.never: "Nunca"
page.cmdb_dashboard.no_overdue: "Todas las revisiones BIA están al día"
page.cmdb_dashboard.no_most_depended: "No se encontraron relaciones de dependencia"
page.asset_detail.impact_radius: "Radio de Impacto"
page.asset_detail.impact_total: "Total"
```

**Acceptance Criteria:**
- [x] All 17 i18n keys added in Spanish
- [x] Keys match TASK-017 keys exactly

---

## Dependency Graph

```
TASK-001 (Asset repo interface)     TASK-002 (CI repo interface)     TASK-017 (i18n EN)   TASK-018 (i18n ES)
    │                                    │
    ├──── TASK-003 (Asset repo impl)     ├──── TASK-004 (CI repo impl)
    │                                    │
    ├────────────┬───────────────────────┘
    │            │
    │     TASK-005 (Impact query)    TASK-006 (Dashboard query)
    │            │                         │
    │            └──────────┬──────────────┘
    │                       │
    │                TASK-007 (Schemas)
    │                       │
    │                TASK-008 (Endpoints)
    │                       │
    │            ┌──────────┼───────────────┐
    │            │          │               │
    │      TASK-009     TASK-010       TASK-013 (TS types)
    │     (Impact        (Dashboard        │
    │      tests)         tests)     ┌─────┼──────┐
    │            │          │        │     │      │
    │      TASK-011    TASK-012  TASK-014  TASK-015
    │     (Impact       (Dashboard (CMDB   (Asset detail
    │     integ.)       integ.)   page)    enhancement)
    │                              │
    │                        TASK-016 (Nav + route)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002, TASK-017, TASK-018
**Batch 2 (Parallel):** TASK-003, TASK-004
**Batch 3 (Parallel):** TASK-005, TASK-006
**Batch 4:** TASK-007
**Batch 5:** TASK-008, TASK-013
**Batch 6 (Parallel):** TASK-009, TASK-010, TASK-011, TASK-012, TASK-014, TASK-015
**Batch 7:** TASK-016

## Final Checklist

- [x] All 18 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] mypy passes (`make lint`)
- [x] TypeScript clean (`npx tsc --noEmit`)
- [x] `GET /cmdb-dashboard` registered BEFORE `GET /{asset_id}` in router
- [x] CMDB Dashboard page accessible at `/cmdb/dashboard` for admin role
- [x] Impact radius badges visible on asset detail Dependencies tab
