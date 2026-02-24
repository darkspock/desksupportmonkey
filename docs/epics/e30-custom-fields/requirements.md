# Epic E30: Custom Fields

**Date:** 2026-02-24
**Priority:** High
**Status:** Draft
**Bounded Context:** `custom_field_bc`
**Plan Gate:** Enterprise (`custom_fields` — already declared in `plan_gate.py`)

---

## Business Alignment

**Objective:** Enable companies to extend the data model of assets, service requests, and incidents with admin-defined custom fields, eliminating the need for external spreadsheets and allowing each organization to capture domain-specific metadata without code changes.

**KPI Targets:**
- Companies with custom fields configured show 30% higher asset data completeness
- Zero code deployments required for customer-specific data requirements
- Custom field values searchable and filterable in list views
- Custom fields appear in PDF/CSV exports

**Evidence:**
- Top-3 feature request from Enterprise prospects: "We need to track [X] on assets but there's no field for it"
- Common examples: cost center, insurance policy number, IMEI, warranty provider, internal asset tag, building/floor, employee department code
- Competitors (Snipe-IT, Asset Panda) offer custom fields as a core differentiator
- NIS2/ISO 27001 auditors often require organization-specific metadata on assets and incidents

---

## Problem Statement

**Current situation:** The platform has a fixed schema for assets, requests, and incidents. Organizations with unique tracking needs (cost centers, insurance numbers, compliance tags, internal codes) resort to stuffing data into the `notes` text field or maintaining parallel spreadsheets.

| Pain Point | Impact |
|-----------|--------|
| Fixed asset schema | Cannot capture org-specific metadata (cost center, insurance, IMEI) |
| Notes field abuse | Unstructured text, not searchable or filterable |
| External spreadsheets | Data drift, duplicate maintenance, audit gaps |
| No per-org customization | Every customer gets the same fields regardless of industry |
| Request metadata gaps | IT teams can't add structured intake fields (e.g., "Urgency reason", "Budget code") |

**Who is affected:**
- **Admins:** Need to define custom fields per entity type for their organization
- **Technicians:** Need to fill in and view custom fields on assets and requests
- **Employees:** See relevant custom fields when creating requests
- **Auditors:** Need custom metadata in exports for compliance evidence

---

## Non-Goals (Out of Scope)

- **Conditional field visibility** — Show/hide fields based on other field values (deferred to E31 Workflow Automations)
- **Custom field-based automations** — Trigger actions when custom field values change (E31 scope)
- **Custom fields on companies or users** — Only assets, requests, and incidents in v1
- **Calculated fields** — Fields whose value is derived from formulas
- **File upload fields** — Attachment-type custom fields (can be added later)
- **Multi-language field labels** — Admin defines labels in one language; i18n for field labels is out of scope
- **Role-based field visibility** — Deferred. However, each field definition has a `visible_to_employees` flag (default: true) controlling whether employees see the field on request forms

---

## Proposed Solution

A new `custom_field_bc` bounded context implementing JSON-based custom field storage with:

1. **Field definitions** — Admin-configurable schema: field name, type, options, required flag, sort order, per entity type (stored in a dedicated `custom_field_definitions` table)
2. **Field values** — Stored as a `JSONB` column (`custom_fields_data`) directly on each target entity table (assets, requests, incidents). Format: `{"field_key": value, ...}`
3. **Frontend dynamic rendering** — Custom fields rendered dynamically in create/edit forms and detail pages
4. **Search & filter** — Custom field values searchable in list views via PostgreSQL JSONB operators
5. **Export integration** — Custom fields included in PDF/CSV reports

### Architecture Decisions

1. **Separate bounded context for definitions** — Custom field definitions span multiple entity types. A dedicated `custom_field_bc` manages the schema (what fields exist, their types, options, validation rules). The actual values live on each target entity.

2. **JSON column on each entity** — Field values are stored as a `JSONB` column on the target entity's table (e.g., `assets.custom_fields_data`). This eliminates JOINs on reads, makes saves atomic (values are part of the entity row), and automatically handles orphan cleanup (when the entity is deleted, its custom field data goes with it).

3. **Field definitions are soft-deleted** — Deactivating a field hides it from forms but preserves historical values in the entity's JSON column. Reactivating restores it.

4. **Integration via response enrichment** — When loading an asset/request/incident, the router reads the entity's `custom_fields_data` JSON and pairs it with the active field definitions to produce a rich response (with labels, types, options). The domain entity carries the raw JSON; the HTTP layer enriches it.

5. **Multi-select as JSON array** — Multi-select field values are stored as a JSON array within the entity's `custom_fields_data` column (e.g., `{"tags": ["Option A", "Option C"]}`).

---

### User Stories

#### Admin — Field Management

**US-001: Define custom fields**
As an admin, I can create custom field definitions for assets, requests, or incidents, specifying the field type, label, options, and whether it's required.

**Acceptance Criteria:**
- [ ] Field types: `text`, `number`, `date`, `select`, `multi_select`, `boolean`
- [ ] For `select` and `multi_select`: admin defines the list of options
- [ ] Admin sets: label (display name), field key (auto-generated slug from label), description (optional), required flag
- [ ] Admin can reorder fields (sort_order)
- [ ] Maximum 20 custom fields per entity type per company
- [ ] Enterprise plan required

**US-002: Edit custom fields**
As an admin, I can edit a custom field definition (label, description, options, required) after creation.

**Acceptance Criteria:**
- [ ] Label, description, required flag, and options are editable
- [ ] Field type cannot be changed after creation (would break existing values)
- [ ] Adding options to a select field is allowed; removing an option that has existing values shows a warning
- [ ] Changes take effect immediately on all forms and views

**US-003: Deactivate/reactivate custom fields**
As an admin, I can deactivate a custom field to hide it from forms, and reactivate it later.

**Acceptance Criteria:**
- [ ] Deactivated fields are hidden from create/edit forms
- [ ] Deactivated field values are preserved and still visible in detail views (grayed out, labeled "Inactive")
- [ ] Reactivating a field restores it to forms
- [ ] Deactivated fields are excluded from required validation

**US-004: Delete custom fields**
As an admin, I can permanently delete a custom field and all its values.

**Acceptance Criteria:**
- [ ] Confirmation dialog with warning about permanent data loss
- [ ] Deletes the field definition; orphaned keys in entity JSONB are ignored on read (cleaned up lazily or via background task)
- [ ] Cannot be undone

#### Technician/Employee — Field Usage

**US-005: Fill custom fields on create**
As a technician, when creating an asset (or request/incident), I see the custom fields defined for that entity type and can fill them in.

**Acceptance Criteria:**
- [ ] Custom fields appear after standard fields in the create form
- [ ] Each field renders according to its type (text input, number input, date picker, select dropdown, checkbox, multi-select)
- [ ] Required fields block form submission if empty
- [ ] Select fields show the admin-defined options
- [ ] Multi-select renders as checkboxes or multi-select dropdown

**US-006: Edit custom fields**
As a technician, when editing an asset (or request/incident), I can modify custom field values.

**Acceptance Criteria:**
- [ ] Custom fields appear in the edit form, pre-filled with current values
- [ ] Same validation as on create
- [ ] Changes are saved alongside the entity update

**US-007: View custom fields on detail page**
As a user viewing an asset/request/incident detail page, I see custom field values displayed in a dedicated section.

**Acceptance Criteria:**
- [ ] Custom fields section appears after standard fields
- [ ] Section header: "Custom Fields" (or i18n equivalent)
- [ ] Fields displayed as label: value pairs
- [ ] Empty fields show "—"
- [ ] Boolean fields show "Yes"/"No"
- [ ] Date fields formatted consistently with the rest of the app
- [ ] Multi-select values shown as comma-separated badges

**US-008: Filter by custom fields**
As a technician, I can filter the asset/request list by custom field values.

**Acceptance Criteria:**
- [ ] Custom select/boolean fields appear as additional filter dropdowns in list views
- [ ] Text/number custom fields searchable via the main search input
- [ ] Filters work alongside existing standard filters

---

## Entities

### CustomFieldDefinition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | ULID | Yes | Primary key |
| company_id | ULID | Yes | Tenant isolation |
| entity_type | Enum | Yes | `asset`, `request`, `incident` |
| field_key | String(50) | Yes | Machine-readable key (auto-slug from label) |
| label | String(255) | Yes | Display label |
| description | String(500) | No | Help text shown below the field |
| field_type | Enum | Yes | `text`, `number`, `date`, `select`, `multi_select`, `boolean` |
| options | JSON | No | For select/multi_select: `["Option A", "Option B", ...]` |
| required | Boolean | Yes | Whether the field is required on create/edit |
| sort_order | Integer | Yes | Display order (0-based) |
| is_active | Boolean | Yes | False = hidden from forms, values preserved |
| visible_to_employees | Boolean | Yes | If false, employees don't see this field on request forms (default: true) |
| created_at | DateTime | Yes | Auto-set |
| updated_at | DateTime | Yes | Auto-updated |

**Indexes:** `(company_id, entity_type)`, unique `(company_id, entity_type, field_key)`

**Validation Rules:**
- `field_key` auto-generated from `label`: lowercase, spaces → underscores, strip special chars, max 50 chars
- `options` required when `field_type` is `select` or `multi_select`, must have at least 1 option
- `options` must be null/empty for non-select types
- Maximum 20 definitions per `(company_id, entity_type)`

### Custom Field Values (JSONB column on target entities)

Instead of a separate values table, each target entity stores its custom field values in a `custom_fields_data: JSONB` column:

**Column added to:** `assets`, `requests`, `incidents` tables
**Column name:** `custom_fields_data`
**Type:** `JSONB`, default `{}`
**Format:** `{"field_key": value, ...}`

**Value Storage Format:**
| Field Type | JSON Value Type | Example |
|------------|----------------|---------|
| text | string | `{"cost_center": "CC-4200"}` |
| number | number | `{"floor": 3}` |
| date | string (ISO 8601) | `{"warranty_end": "2026-03-15"}` |
| boolean | boolean | `{"is_leased": true}` |
| select | string | `{"condition": "Good"}` |
| multi_select | array of strings | `{"tags": ["Option A", "Option C"]}` |

**Example entity row:**
```json
{
  "id": "01ABC...",
  "brand": "Dell",
  "model": "Latitude 5540",
  "custom_fields_data": {
    "cost_center": "CC-4200",
    "insurance_policy": "POL-2026-0042",
    "condition": "Good",
    "is_leased": true,
    "floor": 3
  }
}
```

---

## Use Cases

### UC-001: Create Custom Field Definition

**Actor:** Admin
**Preconditions:** Enterprise plan, < 20 fields for this entity type
**Postconditions:** Field definition created, visible on forms

**Main Flow:**
1. Admin navigates to Settings > Custom Fields
2. Admin selects entity type tab (Assets / Requests / Incidents)
3. Admin clicks "Add Field"
4. Admin fills: label, type, description (optional), required flag
5. For select/multi_select: admin adds options
6. System auto-generates `field_key` from label
7. System validates uniqueness of `field_key` within company + entity type
8. System saves definition with `sort_order` = last position
9. Field immediately appears on create/edit forms

### UC-002: Set Custom Field Values

**Actor:** Technician (or Employee for requests)
**Preconditions:** Entity exists, custom fields defined for entity type
**Postconditions:** Values saved

**Main Flow:**
1. User opens create or edit form for an asset/request/incident
2. System loads active custom field definitions for this entity type
3. Custom fields render dynamically after standard fields
4. User fills in values
5. System validates: required fields filled, number fields numeric, select values from options list, multi_select values all from options list
6. On save, system upserts custom field values (insert or update)

### UC-003: Query with Custom Fields

**Actor:** Technician
**Preconditions:** Custom fields exist with values
**Postconditions:** Results enriched with custom field data

**Main Flow:**
1. User opens asset/request list page
2. System loads list results from primary BC repository
3. System batch-loads custom field values for the result set
4. Response includes `custom_fields` array on each entity: `[{key, label, type, value}]`
5. Frontend renders custom field columns or values

### UC-004: Reorder Custom Fields

**Actor:** Admin
**Preconditions:** Multiple fields exist for an entity type
**Postconditions:** Sort order updated

**Main Flow:**
1. Admin drags field to new position (or uses up/down arrows)
2. System recalculates sort_order for affected fields
3. Changes reflected immediately on forms

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `app.py` | Register custom fields router | Add `include_router` |
| `adapters/http/api/assets/routers.py` | Enrich asset responses with custom fields | Inject custom field service |
| `adapters/http/api/assets/schemas.py` | Add `custom_fields` to response schemas | Optional list field |
| `adapters/http/api/shipments/routers.py` | N/A | No impact |
| `web/app/src/pages/technician/AssetFormPage.tsx` | Render custom fields in create/edit form | Dynamic field rendering |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Show custom fields section | New section |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Show custom fields section | New section |
| `web/app/src/router.tsx` | Add custom fields admin route | New page |
| `web/app/src/components/layout/Sidebar.tsx` | Add nav entry under Settings | Config subgroup |
| `web/app/src/types/index.ts` | TypeScript interfaces | Custom field types |
| `web/app/src/locales/` | i18n translations | EN + ES (~30 keys) |
| `tests/conftest.py` | Import custom field models | Model registration |
| Report templates | Include custom fields in asset/request reports | Template update |
| `adapters/mcp/server.py` | Include `custom_fields` in asset/request MCP responses | Modify response building |
| `scripts/seed_demo_data.py` | Add sample custom field definitions + values | New seed section |
| CSV import service | Recognize custom field columns by `field_key` | Extend import logic |
| `adapters/http/middleware/audit.py` | Custom field changes tracked in audit trail | Auto-captured (JSONB diff) |

---

## API Endpoints

### Field Definitions (Admin)

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/custom-fields/definitions` | admin | List definitions (filter by entity_type) |
| GET | `/api/v1/custom-fields/definitions/{id}` | admin | Get single definition |
| POST | `/api/v1/custom-fields/definitions` | admin | Create definition |
| PUT | `/api/v1/custom-fields/definitions/{id}` | admin | Update definition |
| DELETE | `/api/v1/custom-fields/definitions/{id}` | admin | Delete definition + values |
| POST | `/api/v1/custom-fields/definitions/{id}/deactivate` | admin | Soft-delete (hide from forms) |
| POST | `/api/v1/custom-fields/definitions/{id}/activate` | admin | Reactivate |
| PUT | `/api/v1/custom-fields/definitions/reorder` | admin | Bulk update sort_order |

### Field Values (embedded in entity endpoints)

Custom field values are stored as a JSONB column on each entity. No separate value endpoints are needed. Instead, existing entity endpoints are modified:

- `POST /api/v1/assets/` → accepts `custom_fields_data: {}` in request body
- `PUT /api/v1/assets/{id}` → accepts `custom_fields_data: {}` in request body
- `GET /api/v1/assets/{id}` → response includes enriched `custom_fields: [...]`
- `GET /api/v1/assets` → each item includes enriched `custom_fields: [...]`
- Same pattern for `/requests/` and `/incidents/`

The enriched `custom_fields` array in responses pairs raw values with field definitions (adding labels, types, options) for frontend rendering.

---

## Response Schema

Custom fields are returned as an array on entity responses:

```json
{
  "id": "01ABC...",
  "brand": "Dell",
  "model": "Latitude 5540",
  "custom_fields": [
    {
      "key": "cost_center",
      "label": "Cost Center",
      "type": "text",
      "value": "CC-4200",
      "required": true
    },
    {
      "key": "insurance_policy",
      "label": "Insurance Policy #",
      "type": "text",
      "value": "POL-2026-0042",
      "required": false
    },
    {
      "key": "asset_condition",
      "label": "Condition",
      "type": "select",
      "value": "Good",
      "options": ["New", "Good", "Fair", "Poor"],
      "required": true
    },
    {
      "key": "is_leased",
      "label": "Leased Equipment",
      "type": "boolean",
      "value": true,
      "required": false
    }
  ]
}
```

---

## Definition of Done

### Functional
- [ ] `custom_field_bc` bounded context created with domain entities, enums, exceptions, repository
- [ ] Field definition CRUD (create, update, delete, deactivate, activate, reorder)
- [ ] Field types: text, number, date, select, multi_select, boolean
- [ ] Field value upsert with type validation
- [ ] Required field validation on value save
- [ ] Max 20 fields per entity type per company enforced
- [ ] Unique field_key per (company, entity_type) enforced
- [ ] Custom field values enriched on asset/request/incident detail responses
- [ ] Custom field values enriched on asset/request list responses
- [ ] Select/boolean custom fields available as filters in list views
- [ ] Text/number custom fields searchable via main search
- [ ] Custom fields included in PDF/CSV export reports
- [ ] Enterprise plan gating on definition management endpoints

### Frontend
- [ ] Admin page: Custom Fields management under Settings
- [ ] Tab view per entity type (Assets, Requests, Incidents)
- [ ] Create/edit field modal with type-specific options
- [ ] Drag-to-reorder or arrow buttons for sort order
- [ ] Dynamic custom field rendering in AssetFormPage (create/edit)
- [ ] Dynamic custom field rendering in request create/edit forms
- [ ] Dynamic custom field rendering in incident create/edit forms
- [ ] Custom fields section on asset/request/incident detail pages
- [ ] Custom field filter dropdowns in list views

### Testing
- [ ] Unit tests: CustomFieldDefinition entity validation (slug generation, max fields, type constraints)
- [ ] Unit tests: CustomFieldValue type coercion and validation
- [ ] Unit tests: All command/query handlers
- [ ] Integration tests: Definition CRUD endpoints
- [ ] Integration tests: Value upsert and retrieval
- [ ] Integration tests: Plan gating returns 402 for non-Enterprise
- [ ] Integration tests: Asset/request enrichment with custom fields

### Infrastructure
- [ ] Alembic migration: `custom_field_definitions` table + `custom_fields_data JSONB` column on `assets`, `requests`, `incidents`
- [ ] Models registered in `tests/conftest.py`
- [ ] i18n keys (EN + ES, ~30 keys)

---

## Time Constraints

**Deadline:** None
**Type:** Soft
**Dependencies:**
- E43 (Billing) — for plan gating (already implemented, `custom_fields` key already exists)
- No blocking dependencies — can start immediately

---

## Resolved Decisions

1. **Separate BC for definitions:** `custom_field_bc` manages field definitions (schema). Values live as JSONB on each target entity.
2. **JSON column storage:** Values stored as `custom_fields_data: JSONB` column directly on `assets`, `requests`, `incidents` tables. No separate values table. No EAV.
3. **Native JSON types:** Values stored in their native JSON types (strings, numbers, booleans, arrays). No text coercion needed.
4. **No orphan cleanup needed:** Since values live on the entity row, deleting an entity automatically deletes its custom field data.
5. **Atomic saves:** Custom field values are saved as part of the entity's own UPDATE/INSERT — same row, same transaction. No partial failure risk.
6. **Field type immutable:** Cannot change a field's type after creation (would break existing values). Admin must delete and recreate.
7. **Max 20 fields per entity type:** Prevents abuse and keeps forms manageable. Can be raised later.
8. **field_key auto-generated:** Slugified from label on creation, immutable after. Ensures stable API references.
9. **Multi-select as JSON array:** Stored as `["A","B"]` natively in the JSONB column.
10. **Plan gating:** Definition management requires Enterprise. Reading custom field values on entities is available to all plans.
11. **Search via JSONB operators:** PostgreSQL `->>'key'` for filtering, GIN index on `custom_fields_data` if performance requires it.
12. **Required fields on existing entities:** Validate only on next save. Existing entities are not retroactively validated. Detail views show a "Missing" indicator for empty required fields.
13. **Select option removal:** Allowed. Existing values are preserved as-is. The removed option cannot be selected again on new edits. Detail view shows the value normally.
14. **Employee field visibility:** Each field definition has a `visible_to_employees` flag (default: true). Admin chooses per field which ones employees see on request forms.
15. **Slug collision:** Return a clear validation error: "A field with a similar name already exists." No auto-suffix.
16. **CSV import:** E30 includes custom field support in CSV import. Custom field columns recognized by `field_key`.
17. **MCP integration:** MCP asset/request tools include `custom_fields` in responses. No new management tools.
18. **Audit trail:** Custom field value changes are captured in the audit log with old and new values.
19. **Seed data:** Demo seed includes 3-5 example custom fields per entity type with sample values.

---

## Open Questions

None — all decisions resolved.
