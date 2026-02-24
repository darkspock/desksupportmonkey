# Solution Design: F3 — Search, Filter & Export

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Scope:** Backend query changes + frontend filter UI + report template changes

## Summary

Add JSONB-based filtering and search to asset/request/incident list endpoints. Add custom field filter dropdowns to frontend list pages. Include custom field values in PDF/CSV export templates. Optionally add GIN index for performance.

## Architecture Decision

PostgreSQL JSONB operators for all queries — no additional search infrastructure needed. The `custom_fields_data` column supports:
- Exact match: `custom_fields_data->>'key' = 'value'` (for select, boolean)
- Text search: `custom_fields_data->>'key' ILIKE '%term%'` (for text, number)
- GIN index: `CREATE INDEX ... USING gin(custom_fields_data)` if performance requires

Filter params use `cf_` prefix convention: `?cf_building=HQ&cf_is_leased=true`.

## Implementation Plan

### 1. Backend: Repository Query Changes

#### Asset Repository (modify)
**File:** `src/asset_bc/asset/infrastructure/repository.py`

Add JSONB filter support to the list/search method:

```python
def find_by_company(self, company_id, ..., custom_field_filters: Optional[dict] = None, ...):
    query = select(AssetModel).where(AssetModel.company_id == company_id)

    # Standard filters...

    # Custom field filters
    if custom_field_filters:
        for key, value in custom_field_filters.items():
            # Exact match for select/boolean
            query = query.where(
                AssetModel.custom_fields_data[key].as_string() == str(value)
            )

    # Text search across custom fields
    if search_term and custom_field_search_keys:
        or_conditions = [
            # Standard field search...
        ]
        for cf_key in custom_field_search_keys:
            or_conditions.append(
                AssetModel.custom_fields_data[cf_key].as_string().ilike(f"%{search_term}%")
            )
        query = query.where(or_(*or_conditions))
```

Same pattern for Request and Incident repositories.

### 2. Backend: Router Changes

#### Asset Router (modify)
**File:** `adapters/http/api/assets/routers.py`

```python
@router.get("/")
async def list_assets(
    request: Request,
    cf_enricher = Depends(get_cf_enrichment_service),
    cf_definition_repo = Depends(get_cf_definition_repo),
    ...
):
    # Extract cf_ query params
    custom_field_filters = {}
    for key, value in request.query_params.items():
        if key.startswith("cf_"):
            custom_field_filters[key[3:]] = value  # strip "cf_" prefix

    # Get searchable text/number field keys for search
    definitions = cf_definition_repo.find_active_by_entity_type(company_id, "asset")
    text_search_keys = [d.field_key for d in definitions if d.field_type in ("text", "number")]

    assets, total = asset_repo.find_by_company(
        ...,
        custom_field_filters=custom_field_filters or None,
        custom_field_search_keys=text_search_keys if search else None,
    )
```

### 3. Backend: Export / Report Changes

#### PDF Reports
Modify Jinja2 report templates to include custom fields section.

**File:** `templates/reports/asset_inventory.html`
```html
{% if asset.custom_fields %}
<div class="custom-fields">
  <h4>Custom Fields</h4>
  <table>
    {% for cf in asset.custom_fields %}
    <tr>
      <td class="label">{{ cf.label }}</td>
      <td>{{ cf.value if cf.value is not none else '—' }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}
```

Same for `request_summary.html` and `incident_report.html`.

#### CSV Export
Modify report data preparation in `core/tasks/reports.py`:
```python
# For CSV: add one column per active custom field definition
definitions = cf_repo.find_active_by_entity_type(company_id, entity_type)
for defn in definitions:
    headers.append(defn.label)
for asset in assets:
    row = [...]
    for defn in definitions:
        row.append(asset.custom_fields_data.get(defn.field_key, ""))
```

### 4. Frontend: Filter UI

#### List Page Changes
**Files:** `AssetListPage.tsx`, request list page, incident list page

Add filter dropdowns for select/boolean custom fields:

```tsx
function CustomFieldFilters({ entityType, onFilterChange }) {
  // Fetch active definitions for this entity type
  const { data: definitions } = useQuery({
    queryKey: ['cf-definitions', entityType],
    queryFn: () => api.get(`/custom-fields/definitions?entity_type=${entityType}`),
  });

  // Render filter dropdowns for select and boolean fields only
  const filterableFields = definitions?.filter(d =>
    d.is_active && ['select', 'boolean'].includes(d.field_type)
  );

  return filterableFields?.map(defn => (
    <select
      key={defn.field_key}
      className="w-[180px] bg-card"
      onChange={(e) => onFilterChange(`cf_${defn.field_key}`, e.target.value)}
    >
      <option value="">{defn.label}</option>
      {defn.field_type === 'boolean' ? (
        <>
          <option value="true">{t('page.custom_fields.yes')}</option>
          <option value="false">{t('page.custom_fields.no')}</option>
        </>
      ) : (
        defn.options?.map(opt => <option key={opt} value={opt}>{opt}</option>)
      )}
    </select>
  ));
}
```

The parent list page passes `cf_*` params as query string parameters to the API.

### 5. Optional: GIN Index Migration

If performance testing shows degradation with JSONB queries at scale:

**File:** `alembic/versions/..._add_gin_index_custom_fields.py`
```python
def upgrade() -> None:
    op.execute("CREATE INDEX ix_assets_cf_data ON assets USING gin(custom_fields_data)")
    op.execute("CREATE INDEX ix_requests_cf_data ON requests USING gin(custom_fields_data)")
    op.execute("CREATE INDEX ix_incidents_cf_data ON incidents USING gin(custom_fields_data)")
```

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/infrastructure/repository.py` | Modify | Add JSONB filter params to list query |
| `src/request_bc/request/infrastructure/repository.py` | Modify | Same |
| `src/incident_bc/incident/infrastructure/repository.py` | Modify | Same |
| `adapters/http/api/assets/routers.py` | Modify | Extract cf_ params, pass to repo |
| `adapters/http/api/requests/routers.py` | Modify | Same |
| `adapters/http/api/incidents/routers.py` | Modify | Same |
| `templates/reports/asset_inventory.html` | Modify | Add custom fields section |
| `templates/reports/request_summary.html` | Modify | Add custom fields |
| `templates/reports/incident_report.html` | Modify | Add custom fields |
| `core/tasks/reports.py` | Modify | Include CF in report data |
| `web/app/src/pages/technician/AssetListPage.tsx` | Modify | Add CF filter dropdowns |
| Request list page | Modify | Same |
| Incident list page | Modify | Same |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | Repository JSONB filter query building | High |
| Integration | Filter assets by select custom field | High |
| Integration | Filter assets by boolean custom field | High |
| Integration | Search assets across text custom fields | High |
| Integration | CSV export includes custom field columns | Medium |
| Performance | List 1000 assets with 20 custom fields + filter | Medium |

## Implementation Order

1. [ ] Repository changes: JSONB filter support (asset, request, incident)
2. [ ] Router changes: extract cf_ params (asset, request, incident)
3. [ ] Integration tests: filter + search
4. [ ] PDF report templates: add custom fields section
5. [ ] CSV export: add custom field columns
6. [ ] Frontend: `CustomFieldFilters` component
7. [ ] Frontend: integrate into asset list page
8. [ ] Frontend: integrate into request + incident list pages
9. [ ] Performance test (optional GIN index)
10. [ ] `make lint` + `npx tsc --noEmit`
