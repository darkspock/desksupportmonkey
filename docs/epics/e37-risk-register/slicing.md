# Epic Slicing: E37 - Risk Register

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Total Features:** 4

## Slicing Rationale

E37 introduces a new bounded context (`risk_bc`) with 4 entities (Risk, MitigationPlan, RiskLink, RiskHistory), a state machine, 5x5 scoring matrix, cross-BC queries, Celery periodic tasks, PDF/CSV export, and full frontend including heat map visualization. The scope requires slicing into vertical features.

Slicing follows **vertical slices by user value**:
- **F0** establishes the foundation (BC, entity, lifecycle, CRUD, scoring) — users can create, assess, and manage risks
- **F1** adds mitigation plans and entity linking — risk treatment tracking with cross-references
- **F2** adds review cadence, alerts, and export — compliance and reporting capabilities
- **F3** adds the dashboard — operational analytics with heat map

Each feature is independently deployable and delivers standalone user value.

## Dependency Graph

```
Feature 0: Risk Foundation
    │
    ├── Feature 1: Mitigations & Links
    │
    ├── Feature 2: Reviews, Alerts & Export
    │
    └── Feature 3: Risk Dashboard
```

All features depend only on F0. No circular or cross-feature dependencies.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Risk Foundation | None | Create, assess, and manage risks with 5x5 scoring matrix, status lifecycle, and audit history | L | Done |
| 1 | Mitigations & Links | F0 | Mitigation plan CRUD with owner assignment + link risks to assets, departments, vendors | M | Done |
| 2 | Reviews, Alerts & Export | F0 | Configurable review cadence, overdue alerts via Celery, PDF/CSV export | M | Done |
| 3 | Risk Dashboard | F0 | Heat map visualization, risk trend chart, summary statistics | M | Done |

## Recommended Order

1. **Feature 0: Risk Foundation** — Must be first. Creates the BC, all core DB tables, Risk entity, scoring matrix, status state machine, CRUD endpoints, risk history, and primary frontend (list/detail/create/edit). All other features extend this.
2. **Feature 1: Mitigations & Links** — Adds risk treatment capability. Mitigation plans with owner assignment give technicians actionable work items. Entity links provide cross-reference visibility.
3. **Feature 2: Reviews, Alerts & Export** — Adds compliance features. Review cadence enforcement satisfies NIS2 audit requirements. PDF/CSV export enables board reporting.
4. **Feature 3: Risk Dashboard** — Analytics layer. Best built last when risks exist to visualize. Heat map and trend chart give management operational visibility.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (all depend only on F0)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- F0 is large (L complexity) because it includes the full risk lifecycle + scoring + frontend. Consider splitting frontend work into sub-tasks within F0.
- F1 cross-BC links (asset_id, department_id, vendor_id) require those BCs to have working list/search queries for name resolution.
- F2 reuses existing WeasyPrint + S3 infrastructure from `report_bc`. If that infrastructure has issues, F2 export is blocked.
- F2 Celery beat configuration must be tested in staging before production to avoid missed review reminders.
- F3 heat map visualization uses recharts (already installed for incident dashboard).
