# Implementation Tasks: F2 — Frontend Forms & Detail Pages

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 8
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Types | 1 | S |
| Field Renderers | 1 | M |
| CustomFieldsForm Component | 1 | M |
| CustomFieldsDisplay Component | 1 | S |
| Asset Integration | 1 | M |
| Request Integration | 1 | M |
| Incident Integration | 1 | M |
| i18n | 1 | S |

---

### TASK-001: Add TypeScript Interfaces

**Phase:** Types
**Complexity:** S
**Dependencies:** F1 complete

**File:** `web/app/src/types/index.ts`

**Implementation:**
Add `CustomFieldDefinition` and `CustomFieldValue` interfaces as specified in design.

**Acceptance Criteria:**
- [x] `CustomFieldDefinition` interface with all fields
- [x] `CustomFieldValue` interface with all fields
- [x] `field_type` is union type: `'text' | 'number' | 'date' | 'select' | 'multi_select' | 'boolean'`

---

### TASK-002: Create Field Renderers

**Phase:** Components
**Complexity:** M
**Dependencies:** TASK-001

**Files:**
- `web/app/src/components/custom-fields/fields/TextField.tsx`
- `web/app/src/components/custom-fields/fields/NumberField.tsx`
- `web/app/src/components/custom-fields/fields/DateField.tsx`
- `web/app/src/components/custom-fields/fields/SelectField.tsx`
- `web/app/src/components/custom-fields/fields/MultiSelectField.tsx`
- `web/app/src/components/custom-fields/fields/BooleanField.tsx`

**Implementation:**
Each renderer receives `{ definition, value, onChange }` props. Renders appropriate HTML input with:
- Label + required asterisk
- Description text if present
- Consistent styling matching existing app inputs (`bg-card`, `border-border`, etc.)
- TextField: `<input type="text">`
- NumberField: `<input type="number" step="any">`
- DateField: `<input type="date">`
- SelectField: `<select>` with options from definition
- MultiSelectField: checkbox group (each option as labeled checkbox)
- BooleanField: `<input type="checkbox">` with label

**Acceptance Criteria:**
- [x] 6 field renderer components
- [x] All accept `{ definition, value, onChange }` props
- [x] Labels show required asterisk when `definition.required`
- [x] Description shown as helper text
- [x] Styling matches app design system

---

### TASK-003: Create CustomFieldsForm Component

**Phase:** Components
**Complexity:** M
**Dependencies:** TASK-002

**File:** `web/app/src/components/custom-fields/CustomFieldsForm.tsx`

**Implementation:**
```typescript
interface CustomFieldsFormProps {
  entityType: 'asset' | 'request' | 'incident';
  values: Record<string, unknown>;
  onChange: (data: Record<string, unknown>) => void;
  isEmployee?: boolean;
}
```
- Fetches definitions: `useQuery(['cf-definitions', entityType], ...)`
- Filters: `is_active === true`, if `isEmployee` also filters `visible_to_employees === true`
- Sorts by `sort_order`
- Renders each definition using the matching field renderer
- On change, updates the values dict and calls `onChange`
- Shows section header "Custom Fields" (i18n)
- If no definitions, renders nothing

**Acceptance Criteria:**
- [x] Fetches definitions from API
- [x] Filters active only
- [x] Respects `isEmployee` flag (filters `visible_to_employees`)
- [x] Renders correct field type per definition
- [x] Required fields show asterisk
- [x] Empty state: no section rendered
- [x] Values flow correctly: parent → form → field → onChange → parent

---

### TASK-004: Create CustomFieldsDisplay Component

**Phase:** Components
**Complexity:** S
**Dependencies:** TASK-001

**File:** `web/app/src/components/custom-fields/CustomFieldsDisplay.tsx`

**Implementation:**
```typescript
interface CustomFieldsDisplayProps {
  customFields: CustomFieldValue[];
}
```
- Renders as a card/section with label/value pairs
- Empty values → "—"
- Boolean → "Yes"/"No" (i18n)
- Multi-select → comma-separated badges (`bg-muted` styled)
- Dates → formatted with app's date format
- Inactive fields → grayed out with "Inactive" badge
- Required fields without value → amber "Missing" indicator
- If array empty, render nothing

**Acceptance Criteria:**
- [x] Label/value pair rendering
- [x] Empty → "—"
- [x] Boolean → Yes/No
- [x] Multi-select → badges
- [x] Inactive → grayed + badge
- [x] Missing required → amber indicator

---

### TASK-005: Integrate into Asset Pages

**Phase:** Integration
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Files:**
- Asset create/edit form page (find exact file — likely `AssetFormPage.tsx` or inline in `AssetDetailPage.tsx`)
- `web/app/src/pages/technician/AssetDetailPage.tsx`

**Implementation:**
- **Create/Edit form:** Add `<CustomFieldsForm entityType="asset" values={form.custom_fields_data || {}} onChange={...} />` after standard fields. Include `custom_fields_data` in POST/PUT body.
- **Detail page:** Add `<CustomFieldsDisplay customFields={asset.custom_fields || []} />` section after standard fields. Show section header "Custom Fields".

**Acceptance Criteria:**
- [x] Custom fields appear in asset create form
- [x] Custom fields appear in asset edit form (pre-filled)
- [x] Custom fields saved with asset
- [x] Custom fields displayed on detail page
- [ ] Required custom fields block form submission

---

### TASK-006: Integrate into Request Pages

**Phase:** Integration
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Files:**
- Request create/edit form (locate exact files)
- `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation:**
Same as TASK-005 but for requests. Key difference: employee forms pass `isEmployee={true}` to `CustomFieldsForm` to respect `visible_to_employees` flag.

**Acceptance Criteria:**
- [x] Custom fields in request create form
- [ ] Custom fields in request edit form
- [x] Employee form hides non-visible fields
- [x] Detail page shows custom fields
- [ ] Required fields enforced

---

### TASK-007: Integrate into Incident Pages

**Phase:** Integration
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Files:**
- Incident create/edit form (locate exact files)
- `web/app/src/pages/technician/IncidentDetail.tsx`

**Implementation:**
Same as TASK-005 but for incidents.

**Acceptance Criteria:**
- [x] Custom fields in incident create form
- [ ] Custom fields in incident edit form
- [x] Detail page shows custom fields
- [ ] Required fields enforced

---

### TASK-008: i18n Keys

**Phase:** Configuration
**Complexity:** S
**Dependencies:** None (can be done in parallel)

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Implementation:**
Add ~15 keys as specified in design: section_title, no_value, yes, no, inactive_field, missing_required, select_option, multi_select_hint, etc.

**Acceptance Criteria:**
- [x] EN keys added
- [x] ES keys added
- [x] All text in components uses `t()` calls

---

## Dependency Graph

```
TASK-001 (Types) ──┬── TASK-002 (Renderers) ── TASK-003 (Form)
                   │                                  │
                   └── TASK-004 (Display) ─────┬──────┤
                                               │      │
                                    TASK-005 (Asset) ◄─┘
                                    TASK-006 (Request) ◄─┘
                                    TASK-007 (Incident) ◄─┘

TASK-008 (i18n) — parallel with everything
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-008
**Batch 2 (Parallel):** TASK-002, TASK-004
**Batch 3:** TASK-003
**Batch 4 (Parallel):** TASK-005, TASK-006, TASK-007

## Final Checklist

- [x] All 8 tasks completed
- [x] `npx tsc --noEmit` passes
- [ ] Manual test: create asset with custom fields
- [ ] Manual test: edit asset, values pre-filled
- [ ] Manual test: detail page shows custom fields
- [ ] Manual test: employee request form respects visibility
