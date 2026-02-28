# Epic Slicing: E33 — Endpoint Change Management

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-27
**Total Features:** 4

## Slicing Rationale

E33 creates a new `change_bc` bounded context with four entities (ChangeRequest, ChangeEvent, PostImplementationReview, ChangeAsset) and an 8-state lifecycle with approval workflow. The slicing follows **vertical slices by capability**:

- **F0** establishes the ChangeRequest entity with full CRUD, the complete status state machine (including approval/rejection), the ChangeEvent audit trail, and the list/detail frontend pages — the foundational capability that all other features build on. This single feature delivers full DORA Art. 9 compliance value: formal change tracking with approval, rollback plan, and audit trail.
- **F1** adds ChangeAsset linking (M2M cross-BC) — a self-contained extension that tracks which endpoints are affected by each change.
- **F2** adds PostImplementationReview as a sub-entity — captures outcome, lessons learned, and follow-up actions. Enforces PIR requirement for emergency changes before closing.
- **F3** adds the change dashboard — a reporting layer that aggregates data from F0 for summary cards and upcoming change visibility.

F0 must come first (all features depend on the ChangeRequest entity). F1 and F2 are independent of each other (both only need F0). F3 needs F0 for meaningful dashboard data but is independent of F1/F2.

## Dependency Graph

```
Feature 0: Change Request CRUD + State Machine + List/Detail Pages
    │
    ├── Feature 1: Asset Linking (depends on F0)
    │
    ├── Feature 2: Post-Implementation Review (depends on F0)
    │
    └── Feature 3: Change Dashboard (depends on F0)
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Change Request CRUD + State Machine | None | Full change lifecycle: create, approve/reject, implement, rollback, close. List/detail pages with timeline. DORA Art. 9 compliance baseline | L | Done |
| 1 | Asset Linking | F0 | Link affected assets to changes, view affected assets on detail page | S | Done |
| 2 | Post-Implementation Review | F0 | PIR sub-entity with outcome/lessons/follow-up, enforce PIR for emergency type before close | S | Done |
| 3 | Change Dashboard | F0 | Summary cards, changes by status, upcoming scheduled changes, recently implemented | M | Done |

## Recommended Order

1. **Feature 0: Change Request CRUD + State Machine** — Must be first. Creates the `change_bc` bounded context, all enums, the ChangeRequest entity with full state machine (DRAFT through CLOSED/REJECTED/ROLLED_BACK), ChangeEvent audit trail, approval/rejection workflow, and the list/detail frontend pages. Delivers standalone DORA compliance value.

2. **Feature 1: Asset Linking** — Adds ChangeAsset join table and link/unlink commands. Small scope, extends the detail page with an affected assets section. Placed second because it enriches the core change data.

3. **Feature 2: Post-Implementation Review** — Adds PIR entity and creation command. Extends the detail page with a PIR section and enforces PIR for emergency type. Placed third because it completes the full ITIL-like change lifecycle.

4. **Feature 3: Change Dashboard** — Last because it's a read-only reporting layer that aggregates data from F0. Most useful after changes have been flowing through the system.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F1, F2, F3 all depend only on F0)
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- F0 is relatively large (new BC, 2 entities, 8-state machine, approval workflow, 2 frontend pages). However, the patterns are well-established from maintenance_bc and incident_bc — implementation follows existing conventions closely.
- F0 alone covers DORA Art. 9 requirements. F1-F3 are enhancements. If time pressure is extreme, F0 alone is a valid "done" state for compliance.
- ChangeEvent entity is owned by F0 but written by all features. This is acceptable because it's an append-only audit trail — features only insert, never read/update each other's events.
- No notifications are included in any feature (explicitly deferred in requirements). Can be added as a follow-up feature if needed.
