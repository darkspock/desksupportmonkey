# Solution Design: F2 — Frontend Forms & Detail Pages

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Scope:** Frontend only (React + TypeScript)

## Summary

Build reusable `<CustomFieldsForm>` and `<CustomFieldsDisplay>` components. Integrate into all asset, request, and incident create/edit/detail pages. Respect `visible_to_employees` flag on request forms.

## Architecture Decision

Two shared components under `web/app/src/components/custom-fields/`:
- `CustomFieldsForm` — for create/edit forms. Fetches definitions, renders typed inputs, outputs `custom_fields_data` dict.
- `CustomFieldsDisplay` — for detail pages. Receives enriched `custom_fields` array from API response, renders label/value pairs.

Individual field renderers live in a `fields/` subfolder for clean separation.

## Existing Code Analysis

| Component | Location | Pattern to Follow |
|-----------|----------|-------------------|
| Asset create/edit | `web/app/src/pages/technician/AssetFormPage.tsx` (if exists) or inline in detail page | Form with useState + mutation |
| Asset detail | `web/app/src/pages/technician/AssetDetailPage.tsx` | Sections with label/value pairs |
| Request detail | `web/app/src/pages/technician/RequestDetailPage.tsx` | Same pattern |
| Incident detail | `web/app/src/pages/technician/IncidentDetail.tsx` | Same pattern |
| Design tokens | `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border` | Semantic CSS tokens |
| i18n | `useI18n()` hook, `t('key')` | All text through i18n |
| API | `api.get('/custom-fields/definitions?entity_type=X')` | TanStack useQuery |

## Implementation Plan

### 1. TypeScript Interfaces

**File:** `web/app/src/types/index.ts`

```typescript
interface CustomFieldDefinition {
  id: string;
  entity_type: string;
  field_key: string;
  label: string;
  description?: string;
  field_type: 'text' | 'number' | 'date' | 'select' | 'multi_select' | 'boolean';
  options?: string[];
  required: boolean;
  sort_order: number;
  is_active: boolean;
  visible_to_employees: boolean;
}

interface CustomFieldValue {
  key: string;
  label: string;
  type: string;
  value: unknown;
  required: boolean;
  is_active: boolean;
  visible_to_employees: boolean;
  options?: string[];
}
```

### 2. CustomFieldsForm Component

**File:** `web/app/src/components/custom-fields/CustomFieldsForm.tsx`

```typescript
interface CustomFieldsFormProps {
  entityType: 'asset' | 'request' | 'incident';
  values: Record<string, unknown>;  // current custom_fields_data
  onChange: (data: Record<string, unknown>) => void;
  isEmployee?: boolean;  // filter by visible_to_employees
}

export function CustomFieldsForm({ entityType, values, onChange, isEmployee }: CustomFieldsFormProps) {
  // 1. Fetch active definitions: GET /custom-fields/definitions?entity_type={entityType}
  // 2. Filter by visible_to_employees if isEmployee
  // 3. Sort by sort_order
  // 4. Render each field based on field_type
  // 5. On change, call onChange with updated data dict
}
```

**Field Renderers** (one per type):
- `TextField` — `<input type="text">`
- `NumberField` — `<input type="number" step="any">`
- `DateField` — `<input type="date">`
- `SelectField` — `<select>` with options
- `MultiSelectField` — checkboxes group
- `BooleanField` — `<input type="checkbox">`

Each renderer follows the pattern:
```typescript
interface FieldProps {
  definition: CustomFieldDefinition;
  value: unknown;
  onChange: (value: unknown) => void;
}
```

### 3. CustomFieldsDisplay Component

**File:** `web/app/src/components/custom-fields/CustomFieldsDisplay.tsx`

```typescript
interface CustomFieldsDisplayProps {
  customFields: CustomFieldValue[];
}

export function CustomFieldsDisplay({ customFields }: CustomFieldsDisplayProps) {
  // Render as a card section with label/value pairs
  // Empty values → "—"
  // Boolean → "Yes"/"No" (i18n)
  // Multi-select → comma-separated badges
  // Inactive fields → grayed out with "Inactive" badge
  // Required fields without value → "Missing" indicator (amber)
}
```

### 4. Integration Points

#### Asset Create/Edit Form
Locate the asset form (likely in AssetDetailPage or a separate form page). Add after standard fields:

```tsx
<CustomFieldsForm
  entityType="asset"
  values={form.custom_fields_data || {}}
  onChange={(data) => setForm({ ...form, custom_fields_data: data })}
/>
```

Include `custom_fields_data` in the POST/PUT body.

#### Asset Detail Page
After standard fields section:

```tsx
{asset.custom_fields && asset.custom_fields.length > 0 && (
  <section>
    <h3>{t('page.custom_fields.section_title')}</h3>
    <CustomFieldsDisplay customFields={asset.custom_fields} />
  </section>
)}
```

#### Request Forms (Employee visibility)
```tsx
<CustomFieldsForm
  entityType="request"
  values={form.custom_fields_data || {}}
  onChange={(data) => setForm({ ...form, custom_fields_data: data })}
  isEmployee={currentUser.role === 'employee'}
/>
```

#### Same pattern for Incident create/edit/detail.

### 5. i18n Keys (~15)

| Key | EN | ES |
|-----|----|----|
| `page.custom_fields.section_title` | Custom Fields | Campos personalizados |
| `page.custom_fields.no_value` | — | — |
| `page.custom_fields.yes` | Yes | Sí |
| `page.custom_fields.no` | No | No |
| `page.custom_fields.inactive_field` | Inactive | Inactivo |
| `page.custom_fields.missing_required` | Missing | Faltante |
| `page.custom_fields.select_option` | Select... | Seleccionar... |
| `page.custom_fields.multi_select_hint` | Select all that apply | Selecciona las que apliquen |

### 6. Styling

Follow existing design system tokens:
- Form section: `bg-card border border-border rounded-lg p-4`
- Labels: `text-sm font-medium text-foreground`
- Descriptions: `text-xs text-muted-foreground`
- Inputs: match existing form inputs in the page
- Required indicator: `text-red-500` asterisk
- Inactive badge: `bg-muted text-muted-foreground`
- Missing indicator: `text-amber-600 dark:text-amber-400`

## Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `web/app/src/components/custom-fields/CustomFieldsForm.tsx` | New | Form component |
| `web/app/src/components/custom-fields/CustomFieldsDisplay.tsx` | New | Display component |
| `web/app/src/components/custom-fields/fields/` | New | 6 field renderers |
| `web/app/src/types/index.ts` | Modify | Add interfaces |
| `web/app/src/pages/technician/AssetDetailPage.tsx` | Modify | Add custom fields section |
| `web/app/src/pages/technician/AssetFormPage.tsx` | Modify | Add form integration (or equivalent) |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Modify | Add custom fields section |
| `web/app/src/pages/technician/IncidentDetail.tsx` | Modify | Add custom fields section |
| Request create/edit pages | Modify | Add form with isEmployee flag |
| Incident create/edit pages | Modify | Add form |
| `web/app/src/locales/en.ts` | Modify | Add ~15 keys |
| `web/app/src/locales/es.ts` | Modify | Add ~15 keys |

## Testing Strategy

No automated frontend tests in the current codebase pattern. Verify:
- `npx tsc --noEmit` — TypeScript compiles clean
- Manual test: create asset with custom fields, verify values saved
- Manual test: edit asset, verify values pre-filled
- Manual test: detail page shows custom fields section
- Manual test: employee form hides non-visible fields
- Manual test: required field blocks submission
- Manual test: inactive field shown grayed out on detail

## Implementation Order

1. [ ] TypeScript interfaces
2. [ ] Individual field renderers (6 files)
3. [ ] `CustomFieldsForm` component
4. [ ] `CustomFieldsDisplay` component
5. [ ] Integrate into asset create/edit form
6. [ ] Integrate into asset detail page
7. [ ] Integrate into request forms (with isEmployee)
8. [ ] Integrate into request detail page
9. [ ] Integrate into incident forms
10. [ ] Integrate into incident detail page
11. [ ] i18n keys (EN + ES)
12. [ ] `npx tsc --noEmit`
