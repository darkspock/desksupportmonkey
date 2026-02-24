# Epic Slicing: E30 Custom Fields

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Total Features:** 4

## Slicing Rationale

The epic is sliced into vertical features that each deliver deployable user value. Feature 0 provides the admin CRUD for field definitions (the core data model + admin UI). Feature 1 integrates custom field storage and enrichment into the existing entity endpoints (assets, requests, incidents). Feature 2 adds dynamic form rendering in the frontend so users can actually fill and view custom fields. Feature 3 adds search/filter and export capabilities.

Each feature builds on the previous but is independently deployable — e.g., after F0, admins can define fields even though they aren't rendered on entity forms yet. After F1, the API returns custom field data. After F2, the full create/edit/view loop works. F3 adds polish (search, filter, export).

## Dependency Graph

```
Feature 0: Definition CRUD (Foundation)
    │
    └── Feature 1: Entity Integration
            │
            └── Feature 2: Frontend Forms & Detail Pages
                    │
                    └── Feature 3: Search, Filter & Export
```

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---------|--------------|-----------------|------------|--------|
| 0 | Definition CRUD | None | Admin can define, edit, reorder, deactivate/delete custom fields per entity type. Full admin UI with tabs. | M | Done |
| 1 | Entity Integration | F0 | JSONB column on assets/requests/incidents. Entity endpoints accept and return custom field data. MCP responses enriched. CSV import supports custom field columns. Audit trail captures changes. Seed data. | L | Done |
| 2 | Frontend Forms & Detail Pages | F1 | Dynamic custom field rendering in create/edit forms and detail pages. Employee visibility flag respected. | M | Done |
| 3 | Search, Filter & Export | F2 | Custom field values searchable/filterable in list views. Custom fields in PDF/CSV exports. | M | Done |

## Recommended Order

1. **Feature 0: Definition CRUD** — Must be first. Creates the BC, domain entities, repository, migration, API, admin UI page. All other features depend on field definitions existing.
2. **Feature 1: Entity Integration** — Adds `custom_fields_data` JSONB column to target entities. Modifies entity endpoints to accept/return custom field data. Backend-complete.
3. **Feature 2: Frontend Forms & Detail Pages** — Dynamic field rendering components. The main frontend work. After this, the feature is fully usable end-to-end.
4. **Feature 3: Search, Filter & Export** — Polish features: JSONB-based filtering in list views, export integration. Can be shipped independently after F2.

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1 → F2 → F3)
- [x] Each feature independently deployable
- [x] Vertical slices (each feature has backend + frontend where needed)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

## Risk Notes

- **F1 touches 3 existing BCs** (asset, request, incident) — migration adds a JSONB column to 3 existing tables. Low risk but test carefully.
- **F2 dynamic form rendering** is the most complex frontend piece. Consider using a shared `<CustomFieldsForm>` component to avoid duplication across asset/request/incident forms.
- **F3 JSONB filtering** performance depends on data volume. GIN index on `custom_fields_data` may be needed at scale.
