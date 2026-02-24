# Implementation Tasks: F3 — Search, Filter & Export

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 8
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Infrastructure - Repository JSONB queries | 1 | M |
| HTTP - Router filter params | 1 | M |
| PDF Report Templates | 1 | M |
| CSV Export | 1 | M |
| Frontend - Filter Component | 1 | M |
| Frontend - List Page Integration | 1 | M |
| Optional - GIN Index | 1 | S |
| Tests | 1 | M |

---

### TASK-001: Add JSONB Filter Support to Repositories

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** F2 complete

**Files:**
- `src/asset_bc/asset/infrastructure/repository.py`
- `src/request_bc/request/infrastructure/repository.py`
- `src/incident_bc/incident/infrastructure/repository.py`

**Implementation:**
Add `custom_field_filters: Optional[dict[str, str]]` and `custom_field_search_keys: Optional[list[str]]` parameters to list/find methods.

For exact filters (select/boolean):
```python
if custom_field_filters:
    for key, value in custom_field_filters.items():
        query = query.where(
            Model.custom_fields_data[key].as_string() == str(value)
        )
```

For text search:
```python
if search_term and custom_field_search_keys:
    cf_conditions = [
        Model.custom_fields_data[k].as_string().ilike(f"%{search_term}%")
        for k in custom_field_search_keys
    ]
    # Add to existing OR search conditions
```

**Acceptance Criteria:**
- [x] Asset repo supports `custom_field_filters` param
- [x] Asset repo supports `custom_field_search_keys` for text search
- [x] Same for request and incident repos
- [x] JSONB operators used correctly (`->>'key'`)
- [x] Filters combine with existing standard filters

---

### TASK-002: Update Routers to Extract cf_ Params

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-001

**Files:**
- `adapters/http/api/assets/routers.py`
- Request router
- Incident router

**Implementation:**
In list endpoints, extract `cf_*` query params from `request.query_params`:
```python
custom_field_filters = {
    k[3:]: v for k, v in request.query_params.items() if k.startswith("cf_")
}
```
Load active definitions to get text/number field keys for search scope. Pass both to repository.

**Acceptance Criteria:**
- [x] `cf_` params extracted from query string
- [x] Passed to repository as `custom_field_filters`
- [x] Text/number field keys loaded for search scope
- [x] Works alongside existing filters (status, type, search, etc.)

---

### TASK-003: Update PDF Report Templates

**Phase:** Reports
**Complexity:** M
**Dependencies:** F1 enrichment service

**Files:**
- `templates/reports/asset_inventory.html`
- `templates/reports/request_summary.html`
- `templates/reports/incident_report.html`

**Implementation:**
Add custom fields section to each template:
```html
{% if item.custom_fields %}
<div class="custom-fields-section">
  <h4>Custom Fields</h4>
  {% for cf in item.custom_fields %}
  <div class="field-row">
    <span class="label">{{ cf.label }}:</span>
    <span class="value">
      {% if cf.value is none %}—
      {% elif cf.type == 'boolean' %}{{ 'Yes' if cf.value else 'No' }}
      {% elif cf.type == 'multi_select' %}{{ cf.value | join(', ') }}
      {% else %}{{ cf.value }}
      {% endif %}
    </span>
  </div>
  {% endfor %}
</div>
{% endif %}
```

**Acceptance Criteria:**
- [x] Asset inventory report includes custom fields
- [x] Request summary report includes custom fields (N/A — summary-only report with no individual rows)
- [x] Incident report includes custom fields (N/A — single-incident NIS2 regulatory report with pre-resolved fields)
- [x] Boolean displayed as Yes/No
- [x] Multi-select as comma-separated
- [x] Empty values as "—"

---

### TASK-004: Update CSV Export

**Phase:** Reports
**Complexity:** M
**Dependencies:** F1 enrichment service

**File:** `core/tasks/reports.py` (or wherever CSV export is generated)

**Implementation:**
1. Load active custom field definitions for the entity type
2. Add one CSV column per definition (using `label` as column header)
3. For each entity row, extract value from `custom_fields_data` using `field_key`
4. Format: booleans as "Yes"/"No", multi_select as comma-separated, dates as ISO

**Acceptance Criteria:**
- [x] CSV headers include custom field labels
- [x] Values correctly extracted from JSONB
- [x] Types formatted appropriately
- [x] Empty values as empty string

---

### TASK-005: Create CustomFieldFilters Component

**Phase:** Frontend
**Complexity:** M
**Dependencies:** F2 TASK-001 (types)

**File:** `web/app/src/components/custom-fields/CustomFieldFilters.tsx`

**Implementation:**
```typescript
interface CustomFieldFiltersProps {
  entityType: 'asset' | 'request' | 'incident';
  filters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}
```
- Fetch active definitions for entity type
- Filter to only `select` and `boolean` field types
- Render a `<select>` dropdown per filterable field
- Select fields: options from definition + "All" default
- Boolean fields: options "All", "Yes", "No"
- On change, call `onFilterChange('cf_' + field_key, value)`

**Acceptance Criteria:**
- [x] Fetches definitions
- [x] Only shows select + boolean fields
- [x] Select dropdown per field with options
- [x] Boolean dropdown with Yes/No
- [x] "All" default option clears filter
- [x] Styling matches existing filter dropdowns

---

### TASK-006: Integrate Filters into List Pages

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-005

**Files:**
- `web/app/src/pages/technician/AssetListPage.tsx`
- Request list page
- Incident list page

**Implementation:**
Add `<CustomFieldFilters>` component alongside existing filters. Merge `cf_*` params into the API query string. When a filter changes, re-fetch the list with the new params.

**Acceptance Criteria:**
- [x] Custom field filters visible on asset list page
- [x] Filters trigger API re-fetch with `cf_*` params
- [x] Filters work alongside standard filters
- [x] Same for request and incident list pages
- [x] Clear filter resets to "All"

---

### TASK-007: Optional GIN Index

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**File:** `alembic/versions/..._add_gin_index_custom_fields.py` (create only if performance testing requires it)

**Implementation:**
```python
def upgrade() -> None:
    op.execute("CREATE INDEX ix_assets_cf_data ON assets USING gin(custom_fields_data)")
    op.execute("CREATE INDEX ix_requests_cf_data ON requests USING gin(custom_fields_data)")
    op.execute("CREATE INDEX ix_incidents_cf_data ON incidents USING gin(custom_fields_data)")
```

**Acceptance Criteria:**
- [ ] GIN index on all 3 tables (deferred — not needed until performance testing shows >300ms)
- [ ] Only create if performance testing shows need (>300ms for 1000 entities with filters)

---

### TASK-008: Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-002

**Files:**
- `tests/integration/test_custom_fields_filtering.py`

**Integration tests:**
- GET assets with `cf_building=HQ` → only matching assets returned
- GET assets with `cf_is_leased=true` → filtered correctly
- GET assets with search term that matches custom text field → found
- GET assets with `cf_` filter + standard filter combined → both applied
- GET assets with `cf_nonexistent_key=X` → ignored (no error, no filter)

**Acceptance Criteria:**
- [x] Select filter test
- [x] Boolean filter test
- [x] Text search across custom fields test
- [x] Combined filter test
- [x] Unknown filter key ignored
- [ ] `make test-integration` passes

---

## Dependency Graph

```
TASK-001 (Repo JSONB) → TASK-002 (Router params) → TASK-008 (Tests)
                                                  ↗
TASK-003 (PDF) ─────── parallel ─────────────────
TASK-004 (CSV) ─────── parallel ─────────────────
TASK-005 (Filter Component) → TASK-006 (List Pages)
TASK-007 (GIN Index) — conditional, parallel
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-003, TASK-004, TASK-005
**Batch 2 (Parallel):** TASK-002, TASK-006
**Batch 3:** TASK-008
**Batch 4 (Conditional):** TASK-007

## Final Checklist

- [x] All tasks completed (TASK-007 GIN index deferred)
- [x] `make test` passes (1673 unit tests)
- [ ] `make test-integration` passes
- [ ] `make lint` passes
- [x] `npx tsc --noEmit` passes
- [x] Asset list page: custom field filters work
- [x] PDF reports: custom fields section visible
- [x] CSV export: custom field columns present
- [ ] Performance: list with filters < 300ms for 1000 entities
