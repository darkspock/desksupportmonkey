# Feature F2: Impact Propagation & CMDB Dashboard

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F0 (criticality/BIA fields), F1 (CI relationships)
**Complexity:** L

## Scope

### Included
- Impact propagation queries: upstream dependencies (recursive), downstream impact (recursive), configurable max depth (default: 5)
- Impact radius calculation: count of unique downstream assets grouped by criticality level
- GET `/api/v1/assets/{id}/impact` endpoint — returns upstream dependencies, downstream impact, impact radius
- CMDB dashboard query + handler aggregating: criticality distribution, orphan critical assets, BIA coverage %, total relationships, most-depended-upon assets, overdue BIA reviews
- GET `/api/v1/assets/cmdb-dashboard` endpoint (admin only)
- Frontend: CMDBDashboardPage with summary cards, tables, bar chart
- Frontend: route `/cmdb/dashboard` + sidebar entry under Operations section
- Frontend: enhance Dependencies tab on asset detail page with impact radius summary
- Unit tests for impact propagation and dashboard query
- Integration tests for both new endpoints
- i18n EN/ES for dashboard and impact labels

### Excluded (in other features)
- Criticality/BIA fields (F0)
- CIRelationship CRUD (F1)
- Affected assets on requests (F3)
- SLA escalation (F3)

## User Value

When this feature is complete:
- Technicians can trace the full upstream/downstream dependency chain for any asset — see what breaks if this asset fails and what this asset needs to work
- Admins can see the impact radius (count of affected assets by criticality) for any asset
- Admins can view the CMDB dashboard with infrastructure topology health: criticality distribution, orphan alerts, BIA coverage gaps, and choke-point identification
- Overdue BIA reviews (> 6 months) are visible on the dashboard for proactive review

## Acceptance Criteria

- [ ] Upstream dependency query: returns all assets this asset depends on, recursively up to max depth
- [ ] Downstream impact query: returns all assets that depend on this asset, recursively up to max depth
- [ ] Max traversal depth configurable (default: 5 levels)
- [ ] Cycle detection: recursive traversal does not loop infinitely on circular relationship chains
- [ ] Impact radius: count of unique downstream assets grouped by criticality (critical: N, high: N, medium: N, low: N, unclassified: N)
- [ ] GET `/api/v1/assets/{id}/impact` returns upstream, downstream, and radius data
- [ ] CMDB dashboard: criticality distribution (count per level)
- [ ] CMDB dashboard: orphan critical assets count (criticality=critical, zero relationships)
- [ ] CMDB dashboard: BIA coverage % for Critical/High assets (have impact_score AND rto_minutes)
- [ ] CMDB dashboard: total CI relationships count
- [ ] CMDB dashboard: most-depended-upon assets (top 10 by incoming relationship count)
- [ ] CMDB dashboard: overdue BIA reviews (bia_reviewed_at older than 6 months or null, for Critical/High assets)
- [ ] CMDB dashboard: CI relationships by type (count per type)
- [ ] Frontend: CMDBDashboardPage renders all sections
- [ ] Frontend: Dependencies tab shows impact radius summary (count badges by criticality)
- [ ] Route `/cmdb/dashboard` added, sidebar entry visible to admin
- [ ] Unit tests for impact propagation (flat, nested, cyclic) and dashboard query
- [ ] Integration tests for impact and dashboard endpoints
- [ ] i18n EN/ES translations

## Technical Scope

### Entities (owned by this feature)
- No new entities — uses Asset (F0) and CIRelationship (F1)

### Entities (used from dependencies)
- Asset entity with criticality/BIA fields (F0)
- CIRelationship entity (F1)
- CIRelationshipRepository (F1) — for traversal queries

### Key Components
- `src/asset_bc/asset/application/queries/get_asset_impact.py` — NEW: recursive upstream/downstream + radius
- `src/asset_bc/asset/application/queries/cmdb_dashboard.py` — NEW: aggregation query
- `adapters/http/api/assets/routers.py` — add GET `/{id}/impact` and GET `/cmdb-dashboard`
- `adapters/http/api/assets/schemas.py` — add ImpactResponse, CMDBDashboardResponse schemas
- `web/app/src/pages/admin/CMDBDashboardPage.tsx` — NEW
- `web/app/src/pages/technician/AssetDetailPage.tsx` — enhance Dependencies tab with impact radius
- `web/app/src/config/navSections.ts` — add CMDB dashboard entry
- `web/app/src/components/layout/Sidebar.tsx` — add icon for CMDB dashboard
- `web/app/src/router.tsx` — add CMDB dashboard route

## Notes

- Recursive traversal uses iterative BFS (not recursive function calls) to avoid stack overflow. Visited set prevents infinite loops on cyclic relationships.
- The dashboard "overdue BIA reviews" table shows Critical/High assets where `bia_reviewed_at` is null or older than 6 months. This is the passive reminder mechanism (no Celery task).
- The "most-depended-upon" query counts incoming relationships (where the asset is the target). This identifies infrastructure choke points.
- Impact endpoint is read-only — no side effects, no mutations.
