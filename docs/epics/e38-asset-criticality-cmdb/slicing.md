# Epic Slicing: E38 — Asset Criticality & CMDB

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-26
**Total Features:** 4

## Slicing Rationale

E38 extends the existing `asset_bc/asset` subdomain with criticality classification, CI relationships, and a CMDB dashboard. The slicing follows **vertical slices by capability**:

- **F0** extends the Asset entity with criticality and BIA fields — foundational data that the dashboard and SLA escalation depend on
- **F1** adds the CIRelationship entity with full CRUD — a self-contained capability for dependency mapping
- **F2** adds impact propagation queries and the CMDB dashboard — the reporting/visibility layer that needs both F0 and F1 data
- **F3** adds affected assets on requests and criticality-based SLA escalation — cross-BC integration that needs F0 for criticality data

F0 must come first (other features use criticality). F1 and F3 are independent of each other (both depend only on F0). F2 needs both F0 and F1 because the dashboard shows criticality distribution (F0) AND relationship topology (F1).

## Dependency Graph

```
Feature 0: Criticality & BIA
    │
    ├── Feature 1: CI Relationships
    │       │
    │       └── Feature 2: Impact Propagation & CMDB Dashboard (also depends on F0)
    │
    └── Feature 3: Affected Assets & SLA Escalation
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Criticality & BIA | None (extends E2) | Asset classification by business importance, BIA data for business continuity planning, criticality badge on detail/list pages | M | Done |
| 1 | CI Relationships | F0 | Map infrastructure dependencies between assets, CRUD relationships with constraint enforcement | M | Done |
| 2 | Impact Propagation & CMDB Dashboard | F0, F1 | Upstream/downstream traversal, impact radius, CMDB dashboard with criticality stats, orphan alerts, choke points, overdue BIA reviews | L | Done |
| 3 | Affected Assets & SLA Escalation | F0 | Technician marks affected assets on requests, criticality-based SLA priority escalation | M | Done |

## Recommended Order

1. **Feature 0: Criticality & BIA** — Must be first. Extends Asset entity with the fields all other features depend on. Delivers standalone NIS2 compliance value (asset classification).

2. **Feature 1: CI Relationships** — Adds dependency mapping. Independent from F3. Needed before F2 so the dashboard has relationship data to show.

3. **Feature 3: Affected Assets & SLA Escalation** — Can run in parallel with F1 since it only depends on F0. Delivers the cross-BC integration with request/SLA. Placed before F2 because SLA escalation has higher operational impact than the dashboard.

4. **Feature 2: Impact Propagation & CMDB Dashboard** — Last because it aggregates data from F0 + F1. The dashboard is a reporting layer — it reads data but doesn't produce data that others need.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F2 depends on F0+F1; F1, F3 depend on F0)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- F0 modifies the existing Asset entity/model — migration adds nullable columns, fully backward-compatible.
- F1 creates a new `ci_relationships` table — no impact on existing data.
- F2's recursive dependency traversal must limit depth (default: 5) to prevent performance issues on deeply nested graphs.
- F3 writes to the request's `data` JSON field (no migration needed) but involves cross-BC reads (asset_bc from request detail page, sla_bc from SLA query). These are read-only cross-BC queries — no cross-BC writes.
- F1 and F3 CAN be built in parallel since they don't share files or entities.
