# Feature 3: Search, Filter & Export

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F2
**Complexity:** M

## Scope

### Included
- Custom select/boolean fields appear as filter dropdowns in asset/request/incident list views
- Text/number custom fields searchable via main search input (PostgreSQL JSONB `->>'key'` operators)
- GIN index on `custom_fields_data` column if needed for performance
- Custom field values included in PDF export templates (asset inventory, request summary, incident report)
- Custom field values included in CSV exports
- Frontend: filter dropdowns in list pages for select/boolean custom fields

### Excluded (in other features)
- Everything from F0, F1, F2 (already complete)

## User Value

After this feature, technicians can search and filter entities by custom field values in list views. Custom field data appears in PDF/CSV exports for compliance and reporting. The custom fields feature is fully complete.

## Acceptance Criteria

- [ ] Select custom fields appear as filter dropdowns in asset list page
- [ ] Boolean custom fields appear as filter dropdowns (Yes/No) in asset list page
- [ ] Same filter behavior for request and incident list pages
- [ ] Text/number custom field values searchable via main search input
- [ ] Filters work alongside existing standard filters
- [ ] Asset inventory PDF report includes custom fields section
- [ ] Request summary PDF report includes custom fields
- [ ] Incident report PDF includes custom fields
- [ ] CSV export includes custom field columns (one column per active field)
- [ ] Performance: list queries with custom field filters respond < 300ms for 1000 entities with 20 fields
- [ ] GIN index added if performance testing requires it
- [ ] Unit + integration tests for filter queries
- [ ] `make lint` passes

## Technical Scope

### Key Components
- `src/asset_bc/asset/infrastructure/repository.py` — add JSONB filter support to list query
- `src/request_bc/request/infrastructure/repository.py` — same
- `src/incident_bc/incident/infrastructure/repository.py` — same
- `adapters/http/api/assets/routers.py` — accept custom field filter params
- `adapters/http/api/assets/schemas.py` — filter query params
- Same for request and incident routers
- `templates/reports/asset_inventory.html` — add custom fields section
- `templates/reports/request_summary.html` — add custom fields
- `templates/reports/incident_report.html` — add custom fields
- `core/tasks/reports.py` — include custom fields in report data
- `web/app/src/pages/technician/AssetListPage.tsx` — add custom field filter dropdowns
- Same for request and incident list pages
- Optional: `alembic/versions/..._add_gin_index_custom_fields.py` — GIN index migration

## Notes

- JSONB filtering uses PostgreSQL operators: `custom_fields_data->>'key' = 'value'` for exact match on select/boolean, `custom_fields_data->>'key' ILIKE '%search%'` for text search.
- The filter params are passed as query strings: `?cf_condition=Good&cf_is_leased=true`.
- Frontend dynamically generates filter dropdowns from the active field definitions (fetched once on page load).
