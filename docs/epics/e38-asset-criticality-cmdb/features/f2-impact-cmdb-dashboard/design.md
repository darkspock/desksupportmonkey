# Solution Design: Impact Propagation & CMDB Dashboard

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Bounded Context:** `asset_bc/asset`

## Summary

F2 adds two read-only query capabilities to the existing `asset_bc/asset` subdomain:

1. **Impact propagation** — iterative BFS traversal of CI relationships to find upstream dependencies and downstream impact for a given asset, with cycle detection and configurable max depth (default: 5). Returns traversal results plus an impact radius (unique downstream assets grouped by criticality).

2. **CMDB dashboard** — aggregation query combining asset criticality stats, CI relationship metrics, orphan detection, BIA coverage, and overdue review alerts. Admin-only.

No new entities, no new tables, no migrations. Both features are pure queries reading from existing `assets` and `ci_relationships` tables (created in F0 and F1).

## Architecture Decision

**Approach:** Two new query handlers in the application layer, with new repository methods for SQL-level aggregation.

**Why this approach:**
- BFS traversal runs in-memory after loading all company relationships once (single SQL query), avoiding N+1 per BFS level. Max depth of 5 keeps the result set bounded.
- Dashboard aggregations are SQL `GROUP BY` / `COUNT` queries — not in-memory filtering. Each metric is a single efficient query.
- No new entities or domain events — this is a pure read/reporting layer.

**Alternative considered:** Materializing impact data (pre-computed dependency graph). Rejected — the CI relationship graph is small per company (hundreds, not millions), and BFS on an adjacency list in memory is fast enough for real-time queries.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Asset entity | `src/asset_bc/asset/domain/entities.py` | Yes | No changes |
| CIRelationship entity | `src/asset_bc/asset/domain/entities.py` | Yes | No changes |
| AssetRepositoryInterface | `src/asset_bc/asset/domain/repository.py` | Yes | Add 4 new abstract methods |
| AssetRepository (impl) | `src/asset_bc/asset/infrastructure/repository.py` | Yes | Implement 4 new methods |
| CIRelationshipRepositoryInterface | `src/asset_bc/asset/domain/repository.py` | Yes | Add 4 new abstract methods |
| CIRelationshipRepository (impl) | `src/asset_bc/asset/infrastructure/ci_relationship_repository.py` | Yes | Implement 4 new methods |
| ListCIRelationshipsQuery | `src/asset_bc/asset/application/queries/list_ci_relationships.py` | Pattern reference | — |
| GetSlaDashboardQuery | `src/sla_bc/sla/application/queries/get_dashboard.py` | Pattern reference | — |
| Assets router | `adapters/http/api/assets/routers.py` | Yes | Add 2 new endpoints |
| Assets schemas | `adapters/http/api/assets/schemas.py` | Yes | Add response schemas |
| Assets dependencies | `adapters/http/api/assets/dependencies.py` | Yes | Already has both repos |
| AssetDetailPage | `web/app/src/pages/technician/AssetDetailPage.tsx` | Yes | Add impact radius to Dependencies tab |
| SupplyChainDashboardPage | `web/app/src/pages/admin/SupplyChainDashboardPage.tsx` | Pattern reference | — |
| navSections.ts | `web/app/src/config/navSections.ts` | Yes | Add CMDB dashboard entry |
| Sidebar.tsx | `web/app/src/components/layout/Sidebar.tsx` | Yes | Add CMDB dashboard icon |
| router.tsx | `web/app/src/router.tsx` | Yes | Add CMDB dashboard route |

## Implementation Plan

### 1. Domain Layer

No new entities, enums, or value objects.

#### Repository Interface Extensions

**AssetRepositoryInterface** — add 4 methods to `src/asset_bc/asset/domain/repository.py`:

| Method | Signature | Description |
|--------|-----------|-------------|
| `count_by_criticality` | `(company_id: str) -> dict[str, int]` | Count assets grouped by criticality level. Include `"unclassified"` for NULL criticality. |
| `bia_coverage_stats` | `(company_id: str) -> dict` | Returns `{"total_critical_high": int, "has_bia": int, "coverage_pct": float}`. Has BIA = both `impact_score` AND `rto_minutes` are not null. |
| `count_orphan_critical_assets` | `(company_id: str) -> int` | Count assets with criticality=critical that have zero CI relationships (neither source nor target). Uses NOT EXISTS subquery against `ci_relationships`. |
| `find_overdue_bia_reviews` | `(company_id: str, months: int) -> list[dict]` | Critical/High assets where `bia_reviewed_at IS NULL OR bia_reviewed_at < now() - {months} months`. Returns `[{"id", "name", "asset_tag", "criticality", "bia_reviewed_at"}]`. |

**CIRelationshipRepositoryInterface** — add 4 methods to `src/asset_bc/asset/domain/repository.py`:

| Method | Signature | Description |
|--------|-----------|-------------|
| `find_all_by_company` | `(company_id: str) -> list[CIRelationship]` | All relationships for a company. Used by BFS traversal to load the full graph once. |
| `count_all` | `(company_id: str) -> int` | Total relationship count for dashboard stat card. |
| `count_by_type` | `(company_id: str) -> dict[str, int]` | Count relationships grouped by `relationship_type`. |
| `count_incoming_by_asset` | `(company_id: str, limit: int = 10) -> list[dict]` | Top N assets by incoming relationship count. Returns `[{"asset_id": str, "asset_name": str, "asset_tag": str, "count": int}]`. SQL `GROUP BY target_asset_id ORDER BY count DESC LIMIT N`. Joins `assets` table for name/tag. |

### 2. Application Layer

#### Queries

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| `GetAssetImpactQuery` | `GetAssetImpactQueryHandler` | `src/asset_bc/asset/application/queries/get_asset_impact.py` | BFS traversal for upstream/downstream + impact radius |
| `GetCMDBDashboardQuery` | `GetCMDBDashboardQueryHandler` | `src/asset_bc/asset/application/queries/cmdb_dashboard.py` | Aggregation query for all dashboard metrics |

##### GetAssetImpactQuery

```python
@dataclass
class GetAssetImpactQuery(Query):
    asset_id: str
    company_id: str
    max_depth: int = 5
```

**Handler dependencies:**
- `asset_repo: AssetRepositoryInterface` — to validate asset exists and get criticality data
- `ci_repo: CIRelationshipRepositoryInterface` — to load all relationships for BFS

**Handler algorithm:**
1. Validate `asset_id` exists in company (raise `AssetNotFoundError` if not)
2. Load all relationships: `ci_repo.find_all_by_company(company_id)`
3. Build adjacency maps:
   - `outgoing[source_id] -> [(target_id, relationship)]` (for downstream: "what depends on me")
   - `incoming[target_id] -> [(source_id, relationship)]` (for upstream: "what I depend on")
   - Note: direction semantics — `source DEPENDS_ON target` means source depends on target, so upstream = follow `source_asset_id` field from the starting asset (find relationships where `source_asset_id == asset_id`, then recurse into `target_asset_id`). Downstream = follow `target_asset_id` field (find relationships where `target_asset_id == asset_id`, then recurse into `source_asset_id`).
4. BFS upstream: starting from `asset_id`, find all relationships where `source_asset_id == asset_id`, add `target_asset_id` to queue. Repeat up to `max_depth`. Visited set prevents cycles.
5. BFS downstream: starting from `asset_id`, find all relationships where `target_asset_id == asset_id`, add `source_asset_id` to queue. Repeat up to `max_depth`. Visited set prevents cycles.
6. Load asset details for all discovered IDs: `asset_repo.find_by_ids(all_ids, company_id)`
7. Compute impact radius: count unique downstream assets grouped by criticality (None → "unclassified")

**Return DTO:**

```python
@dataclass
class ImpactAssetDto:
    id: str
    name: str
    asset_tag: Optional[str]
    criticality: Optional[str]
    depth: int  # BFS depth from starting asset
    relationship_type: str  # the relationship connecting to this asset

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
    upstream: list[ImpactAssetDto]  # assets this depends on
    downstream: list[ImpactAssetDto]  # assets that depend on this
    radius: ImpactRadiusDto  # downstream counts by criticality
```

##### GetCMDBDashboardQuery

```python
@dataclass
class GetCMDBDashboardQuery(Query):
    company_id: str
```

**Handler dependencies:**
- `asset_repo: AssetRepositoryInterface`
- `ci_repo: CIRelationshipRepositoryInterface`

**Handler logic:** Call each aggregation method and assemble the DTO. No business logic — pure data retrieval.

**Return DTO:**

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
    # Criticality distribution
    criticality_distribution: dict[str, int]  # {"critical": N, "high": N, ...}
    # Orphan critical assets
    orphan_critical_count: int
    # BIA coverage
    bia_total_critical_high: int
    bia_has_coverage: int
    bia_coverage_pct: float
    # Relationships
    total_relationships: int
    relationships_by_type: dict[str, int]  # {"depends_on": N, "runs_on": N, ...}
    # Top depended-upon
    most_depended_upon: list[MostDependedAssetDto]
    # Overdue BIA reviews
    overdue_bia_reviews: list[OverdueBIAReviewDto]
```

### 3. Infrastructure Layer

#### Repository Implementations

**AssetRepository** — `src/asset_bc/asset/infrastructure/repository.py`:

| Method | SQL Pattern |
|--------|-------------|
| `count_by_criticality` | `SELECT COALESCE(criticality, 'unclassified'), COUNT(*) FROM assets WHERE company_id = ? AND status != 'disposed' GROUP BY 1` |
| `bia_coverage_stats` | `SELECT COUNT(*) FILTER (WHERE criticality IN ('critical','high')) as total, COUNT(*) FILTER (WHERE criticality IN ('critical','high') AND impact_score IS NOT NULL AND rto_minutes IS NOT NULL) as has_bia FROM assets WHERE company_id = ? AND status != 'disposed'` |
| `count_orphan_critical_assets` | `SELECT COUNT(*) FROM assets a WHERE a.company_id = ? AND a.criticality = 'critical' AND a.status != 'disposed' AND NOT EXISTS (SELECT 1 FROM ci_relationships cr WHERE cr.company_id = ? AND (cr.source_asset_id = a.id OR cr.target_asset_id = a.id))` |
| `find_overdue_bia_reviews` | `SELECT id, name, asset_tag, criticality, bia_reviewed_at FROM assets WHERE company_id = ? AND criticality IN ('critical','high') AND status != 'disposed' AND (bia_reviewed_at IS NULL OR bia_reviewed_at < now() - interval '{months} months') ORDER BY criticality, name` |

**CIRelationshipRepository** — `src/asset_bc/asset/infrastructure/ci_relationship_repository.py`:

| Method | SQL Pattern |
|--------|-------------|
| `find_all_by_company` | `SELECT * FROM ci_relationships WHERE company_id = ?` |
| `count_all` | `SELECT COUNT(*) FROM ci_relationships WHERE company_id = ?` |
| `count_by_type` | `SELECT relationship_type, COUNT(*) FROM ci_relationships WHERE company_id = ? GROUP BY 1` |
| `count_incoming_by_asset` | `SELECT cr.target_asset_id, a.name, a.asset_tag, COUNT(*) as cnt FROM ci_relationships cr JOIN assets a ON cr.target_asset_id = a.id WHERE cr.company_id = ? GROUP BY 1,2,3 ORDER BY cnt DESC LIMIT ?` |

#### Migrations

No migrations needed. F2 is read-only over existing tables.

### 4. HTTP Layer

#### Endpoints

| Method | Route | Auth | Handler | Description |
|--------|-------|------|---------|-------------|
| `GET` | `/api/v1/assets/{asset_id}/impact` | TECHNICIAN+ | `GetAssetImpactQueryHandler` | Impact propagation + radius |
| `GET` | `/api/v1/assets/cmdb-dashboard` | ADMIN | `GetCMDBDashboardQueryHandler` | CMDB dashboard data |

**Important:** `GET /cmdb-dashboard` must be registered BEFORE `GET /{asset_id}` in the router to avoid route shadowing. Follow the same pattern as `GET /assignable-users` and `GET /locations`.

#### Schemas — `adapters/http/api/assets/schemas.py`

New Pydantic response models:

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

#### Router additions — `adapters/http/api/assets/routers.py`

```python
@router.get("/cmdb-dashboard")
def get_cmdb_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    asset_repo=Depends(get_asset_repo),
    ci_repo=Depends(get_ci_relationship_repo),
):
    handler = GetCMDBDashboardQueryHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    dto = handler.handle(GetCMDBDashboardQuery(company_id=current_user.company_id))
    return {"data": CMDBDashboardResponse(...).model_dump(mode="json")}

@router.get("/{asset_id}/impact")
def get_asset_impact(
    asset_id: str,
    max_depth: int = Query(default=5, ge=1, le=10),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo=Depends(get_asset_repo),
    ci_repo=Depends(get_ci_relationship_repo),
):
    handler = GetAssetImpactQueryHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    dto = handler.handle(GetAssetImpactQuery(
        asset_id=asset_id,
        company_id=current_user.company_id,
        max_depth=max_depth,
    ))
    return {"data": AssetImpactResponse(...).model_dump(mode="json")}
```

**Endpoint placement:** `GET /cmdb-dashboard` must go BEFORE `GET /{asset_id}` line in the router file. Place it right after the existing `GET /locations` block and before `GET /{asset_id}`.

### 5. Frontend

#### New Page: CMDBDashboardPage

**File:** `web/app/src/pages/admin/CMDBDashboardPage.tsx`

**Pattern:** Follow `SupplyChainDashboardPage.tsx` exactly.

**Sections:**
1. **Stat cards row** (grid 2x4): Total Assets by Criticality (mini badges), Orphan Critical Assets count, BIA Coverage %, Total CI Relationships
2. **Criticality Distribution** — horizontal bar chart (pure CSS bars, like RiskBar in SupplyChainDashboardPage): critical/high/medium/low/unclassified
3. **CI Relationships by Type** — horizontal bar chart: runs_on/depends_on/connected_to/part_of/backs_up
4. **Most Depended-Upon Assets** table (top 10): Asset Name, Asset Tag, Incoming Count
5. **Overdue BIA Reviews** table: Asset Name, Asset Tag, Criticality, Last Reviewed

**Data fetch:** Single `useQuery` to `GET /api/v1/assets/cmdb-dashboard`.

#### Enhancement: AssetDetailPage Dependencies Tab

**File:** `web/app/src/pages/technician/AssetDetailPage.tsx`

Add impact radius summary at the top of the Dependencies tab section, above the existing "Depends On" / "Depended On By" tables.

**Data fetch:** `useQuery` to `GET /api/v1/assets/${id}/impact`.

**UI:** Row of small badge/pill elements showing downstream impact count per criticality level:
```
Impact Radius: [Critical: 3] [High: 5] [Medium: 2] [Low: 1] [Total: 11]
```
Color-coded badges: critical=red, high=orange, medium=yellow, low=green.

Only show if there are downstream dependencies (total > 0).

#### Navigation

**navSections.ts:** Add entry under `nav.section_operations`:
```ts
{ to: '/cmdb/dashboard', labelKey: 'nav.cmdb_dashboard', roles: ['admin', 'super_admin'] },
```

**Sidebar.tsx:** Add icon mapping for `/cmdb/dashboard` path (use a network/topology SVG icon).

**router.tsx:** Add lazy import and route:
```tsx
const CMDBDashboardPage = lazy(() => import('./pages/admin/CMDBDashboardPage'));
// Under admin routes:
{ path: 'cmdb/dashboard', element: <RequireRole roles={['admin', 'super_admin']}><S><CMDBDashboardPage /></S></RequireRole> }
```

#### i18n

**en.ts additions:**
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

**es.ts additions:** Spanish translations for all the above.

### 6. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/repository.py` | Modify | Add 4 methods to AssetRepositoryInterface + 4 methods to CIRelationshipRepositoryInterface |
| `src/asset_bc/asset/infrastructure/repository.py` | Modify | Implement 4 new AssetRepository methods |
| `src/asset_bc/asset/infrastructure/ci_relationship_repository.py` | Modify | Implement 4 new CIRelationshipRepository methods |
| `adapters/http/api/assets/routers.py` | Modify | Add 2 new endpoints (placement before /{asset_id}) |
| `adapters/http/api/assets/schemas.py` | Modify | Add 6 new response schemas |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Modify | Add impact radius to Dependencies tab |
| `web/app/src/config/navSections.ts` | Modify | Add CMDB dashboard nav entry |
| `web/app/src/components/layout/Sidebar.tsx` | Modify | Add icon for CMDB dashboard |
| `web/app/src/router.tsx` | Modify | Add CMDB dashboard route + lazy import |
| `web/app/src/locales/en.ts` | Modify | Add i18n keys |
| `web/app/src/locales/es.ts` | Modify | Add i18n keys |
| `web/app/src/types/index.ts` | Modify | Add CMDBDashboard, AssetImpact TypeScript interfaces |

#### Breaking Changes

None. All changes are additive (new endpoints, new query handlers, new frontend page).

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F0 (Criticality & BIA) | Data | Asset entity must have criticality, BIA fields |
| F1 (CI Relationships) | Data | CIRelationship entity and table must exist |

## Testing Strategy

| Test Type | File | Scope | Priority |
|-----------|------|-------|----------|
| Unit | `tests/unit/asset_bc/asset/application/queries/test_get_asset_impact.py` | BFS traversal: flat, nested, cyclic, max depth, empty, asset not found | High |
| Unit | `tests/unit/asset_bc/asset/application/queries/test_cmdb_dashboard.py` | Dashboard aggregation with mocked repo data | High |
| Integration | `tests/integration/test_asset_impact_endpoints.py` | GET impact endpoint (auth, 200, 404) | Medium |
| Integration | `tests/integration/test_cmdb_dashboard_endpoints.py` | GET dashboard endpoint (auth, 200, empty) | Medium |

### Unit Test Cases: Impact Propagation

1. **No relationships** → empty upstream/downstream, zero radius
2. **Flat dependencies** (depth 1 only) → correct upstream/downstream separation
3. **Nested dependencies** (depth 2-3) → BFS traverses multiple levels, correct depth values
4. **Cycle detection** → A→B→C→A does not infinite loop, each node appears once
5. **Max depth limit** → relationships beyond max_depth are not included
6. **Mixed relationship types** → correct traversal regardless of type
7. **Asset not found** → raises `AssetNotFoundError`
8. **Impact radius calculation** → downstream assets correctly grouped by criticality, None → "unclassified"

### Unit Test Cases: CMDB Dashboard

1. **All metrics populated** → correct DTO assembly
2. **Empty company** → zero counts, empty lists, 0.0 coverage
3. **Orphan calculation** → critical asset with no relationships counted
4. **BIA coverage** → percentage computed correctly (has_bia / total_critical_high * 100)
5. **Overdue BIA reviews** → null and old dates both included

## Implementation Order

1. Domain: Add abstract methods to AssetRepositoryInterface and CIRelationshipRepositoryInterface
2. Infrastructure: Implement new repository methods (AssetRepository + CIRelationshipRepository)
3. Application: `get_asset_impact.py` — BFS traversal query handler
4. Application: `cmdb_dashboard.py` — dashboard aggregation query handler
5. HTTP: Add schemas, endpoints, register before `/{asset_id}`
6. Unit tests: impact propagation + dashboard query
7. Integration tests: both endpoints
8. Frontend: TypeScript types, CMDBDashboardPage, AssetDetailPage enhancement
9. Frontend: router, navSections, Sidebar icon, i18n

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| BFS on large graph slow | Low | Medium | Max depth cap (default 5, max 10). Load all edges once, not per level. |
| Route shadowing (/cmdb-dashboard vs /{asset_id}) | Medium | High | Register /cmdb-dashboard BEFORE /{asset_id} in router — same pattern as /locations |
| Orphan count slow (NOT EXISTS subquery) | Low | Low | Existing indexes on ci_relationships(source_asset_id) and ci_relationships(target_asset_id) cover this |
