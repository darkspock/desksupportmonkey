# Epic Slicing: E31 Workflow Templates with Checklists

**Epic:** [requirement.md](requirement.md)
**Date:** 2026-02-25
**Total Features:** 5

## Slicing Rationale

The epic has two major dimensions: (1) replacing hardcoded request types with dynamic workflow templates, and (2) adding checklist capabilities per template. These are sliced into vertical features that each deliver deployable value.

Feature 0 builds the foundation: the `workflow_bc` bounded context with template CRUD, checklist entities, DB tables, API endpoints, and the admin UI. After F0, admins can create/edit/delete workflow templates with subtypes and checklist item definitions.

Feature 1 connects templates to the request creation flow: NewRequestPage renders types from the API instead of hardcoded config, and creates requests with `workflow_template_id`. The request detail response is enriched with template metadata.

Feature 2 makes the runtime checklist functional: checklist items are generated on request creation, technicians can toggle/assign/add/remove items, the resolution guard blocks resolving with incomplete required items, and the RequestDetailPage shows the checklist card.

Feature 3 updates the remaining frontend: RequestQueuePage shows template names/icons, and installs lucide-react for the icon system.

Feature 4 handles data migration: links existing requests to templates, backfills `workflow_template_id`, and ensures the complete set of 6 default templates with subtypes and icons.

## Dependency Graph

```
Feature 0: Foundation (workflow_bc + admin CRUD)
    │
    ├── Feature 1: Dynamic Request Types (NewRequestPage + request creation)
    │       │
    │       └── Feature 4: Data Migration (backfill existing requests)
    │
    ├── Feature 2: Checklist Runtime (generate, toggle, assign, resolution guard)
    │
    └── Feature 3: Queue & Icons (RequestQueuePage + lucide-react)
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Foundation | None | Admin can create/edit/delete workflow templates with subtypes + checklist definitions. Full admin UI. API + backend complete. | L | Done |
| 1 | Dynamic Request Types | F0 | Employees pick request type from templates API. Requests store `workflow_template_id`. Detail response includes template metadata. | M | Done |
| 2 | Checklist Runtime | F0 | Checklist items auto-generated on request creation. Technicians toggle/assign/add/remove items. Resolution guard. Checklist card in RequestDetailPage. | M | Done |
| 3 | Queue & Icons | F0 | RequestQueuePage shows template name/icon. lucide-react for icon rendering across app. | S | Done |
| 4 | Data Migration | F1 | Existing requests linked to templates. Complete default template set (6 types, subtypes, icons). `workflow_template_id` backfilled. | S | Done |

## Recommended Order

1. **Feature 0: Foundation** — Already done. workflow_bc, admin page, API, 42 unit tests.
2. **Feature 2: Checklist Runtime** — Already done. Generate, toggle, assign, resolution guard, RequestDetailPage card.
3. **Feature 1: Dynamic Request Types** — Next priority. The core value: employees pick from dynamic templates. Requires updating NewRequestPage, request creation flow, and request detail response.
4. **Feature 3: Queue & Icons** — After F1. Visual polish: template names/icons in queue views.
5. **Feature 4: Data Migration** — Last. Links existing requests to templates. Requires F1 to be stable first.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1/F2/F3 → F4)
- [x] Each feature independently deployable
- [x] Vertical slices (each feature has backend + frontend where needed)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F1 modifies NewRequestPage** which is a high-traffic page. Test thoroughly to ensure backward compatibility during transition.
- **F4 data migration** modifies existing service_requests rows. Run in a transaction with verification before committing. Keep old `type`/`subtype` columns as denormalized cache.
- **F3 lucide-react** adds a new dependency. Verify bundle size impact.
