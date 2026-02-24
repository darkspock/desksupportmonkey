# Epic Slicing: E36 - Security Incident Management (NIS2)

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Total Features:** 5

## Slicing Rationale

E36 introduces a new bounded context (`incident_bc`) with 6 entities, a state machine, NIS2 regulatory reporting, cross-BC queries, PDF generation, Celery periodic tasks, and full frontend. The scope is too large for a single delivery cycle.

Slicing follows **vertical slices by user value**:
- **F0** establishes the foundation (BC, entity, lifecycle, CRUD) — users can create and manage incidents
- **F1** adds the NIS2 differentiator (regulatory deadlines, PDF reports, escalations) — the core compliance feature
- **F2** adds asset/vendor cross-referencing — impact visibility
- **F3** adds post-mortem and employee reporting — organizational improvement + broader user access
- **F4** adds the dashboard — operational analytics

Each feature is independently deployable and delivers standalone user value.

## Dependency Graph

```
Feature 0: Incident Foundation
    │
    ├── Feature 1: NIS2 Regulatory Reports
    │
    ├── Feature 2: Asset & Vendor Linking
    │
    ├── Feature 3: Post-Mortem & Employee Reporting
    │
    └── Feature 4: Incident Dashboard
```

All features depend only on F0. No circular or cross-feature dependencies.

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Incident Foundation | None | Create, manage, and track security incidents through full lifecycle with timeline audit trail | L | Done |
| 1 | NIS2 Regulatory Reports | F0 | Countdown timers, PDF report generation, deadline escalation alerts | L | Done |
| 2 | Asset & Vendor Linking | F0 | Cross-reference incidents with affected assets and involved vendors | S | Done |
| 3 | Post-Mortem & Employee Reporting | F0 | Root cause analysis for closed incidents + simplified employee reporting | M | Done |
| 4 | Incident Dashboard | F0 | Real-time operational visibility with MTTC, MTTR, severity distribution | M | Done |

## Recommended Order

1. **Feature 0: Incident Foundation** — Must be first. Creates the BC, all DB tables, core entity, and the primary user experience (create/manage/track incidents). All other features extend this.
2. **Feature 1: NIS2 Regulatory Reports** — Primary business differentiator. NIS2 deadlines with PDF generation and escalation alerts. This is why customers buy the product.
3. **Feature 2: Asset & Vendor Linking** — Adds impact visibility. Quick win (small complexity) that enhances incident detail.
4. **Feature 3: Post-Mortem & Employee Reporting** — Extends the lifecycle with organizational learning + opens incident reporting to all employees.
5. **Feature 4: Incident Dashboard** — Analytics layer. Best built last when there's data to visualize.

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

- F0 is large (L complexity) because it includes the full incident lifecycle + frontend. Consider splitting frontend work into sub-tasks within F0.
- F1 reuses existing WeasyPrint + S3 infrastructure from `report_bc`. If that infrastructure has issues, F1 is blocked.
- F2 depends on cross-BC reads from `asset_bc` and `procurement_bc`. Those BCs must have working list/search queries.
- Celery beat configuration (F1) must be tested in staging before production to avoid missed deadlines.
