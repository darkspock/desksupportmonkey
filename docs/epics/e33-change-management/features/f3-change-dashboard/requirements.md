# Feature: Change Dashboard

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F0
**Complexity:** M

## Scope

### Included

- Dashboard query handler that aggregates change request data
- Summary cards: total open changes, pending approval count, in-progress count, implemented (awaiting close) count, changes scheduled this week
- Changes by status distribution (horizontal bar chart, same pattern as vulnerability dashboard)
- Changes by type distribution (standard/normal/emergency)
- Upcoming scheduled changes (next 30 days) — table with title, type, planned_date, assigned_to
- Recently implemented changes (last 30 days) — table with title, type, implemented_at, outcome (if PIR exists)
- Rolled back changes count (last 90 days) — alert card if > 0
- GET /changes/dashboard endpoint (admin only)
- ChangeDashboardPage.tsx frontend page
- Navigation entry in sidebar
- i18n keys for dashboard

### Excluded (in other features)

- Change Request CRUD and state machine (F0)
- Asset linking data in dashboard (F1)
- PIR outcome aggregation beyond basic count (F2)
- Drag-and-drop calendar (out of epic scope)
- Change conflict detection (out of epic scope)

## User Value

When this feature is complete, admins have a single view showing the current state of all change management activity: what's pending approval, what's scheduled, what was recently implemented, and whether any rollbacks occurred. This supports operational oversight and DORA audit evidence.

## Acceptance Criteria

- [ ] Dashboard shows summary cards: total open, pending approval, in-progress, implemented, scheduled this week
- [ ] Horizontal bar chart for status distribution (all 8 statuses)
- [ ] Horizontal bar chart for type distribution (standard/normal/emergency)
- [ ] Table of upcoming scheduled changes (next 30 days, sorted by planned_date ascending)
- [ ] Table of recently implemented changes (last 30 days, sorted by implemented_at descending)
- [ ] Rolled back changes alert card (count in last 90 days, shown only if > 0)
- [ ] Each table row links to the change detail page
- [ ] Dashboard is admin-only (403 for non-admin)
- [ ] Empty state handled gracefully (zero counts, empty tables)
- [ ] i18n keys for all dashboard labels
- [ ] Unit tests for dashboard query handler
- [ ] Integration test for dashboard endpoint

## Technical Scope

### Entities (owned by this feature)

- None (pure read-only aggregation)

### Entities (used from dependencies)

- **ChangeRequest** (F0) — source data for all metrics

### Key Components

- `src/change_bc/change_request/application/queries/change_dashboard.py` — query handler + DTOs
- `adapters/http/api/changes/routers.py` — add GET /dashboard endpoint (before /{change_id} to avoid route conflict)
- `web/app/src/pages/admin/ChangeDashboardPage.tsx`
- `web/app/src/router.tsx` — add route
- `web/app/src/config/navSections.ts` — add nav entry
- Locales updates (en.ts, es.ts)

## Notes

- Follows the exact same pattern as VulnerabilityDashboardPage and SupplyChainDashboardPage
- Dashboard endpoint must be registered BEFORE the /{change_id} route to avoid "dashboard" being matched as a change_id
- All metrics are computed at query time (no Celery task, no materialized views) — same approach as all other dashboards in the codebase
