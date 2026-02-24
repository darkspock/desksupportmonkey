# Feature 2: Frontend Forms & Detail Pages

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** F1
**Complexity:** M

## Scope

### Included
- Shared `<CustomFieldsForm>` component: renders custom fields dynamically based on definitions
- Field type renderers: text input, number input, date picker, select dropdown, multi-select (checkboxes or multi-select dropdown), boolean checkbox
- Required field client-side validation
- Integration into asset create/edit forms
- Integration into request create/edit forms
- Integration into incident create/edit forms
- Employee visibility: request forms respect `visible_to_employees` flag
- Custom fields section on asset detail page
- Custom fields section on request detail page
- Custom fields section on incident detail page
- Display: label/value pairs, empty shows "—", boolean shows "Yes"/"No", dates formatted consistently, multi-select as comma-separated badges
- Inactive fields shown grayed out with "Inactive" label on detail pages
- "Missing" indicator for required fields without values on existing entities
- TypeScript interfaces for custom field types
- i18n keys (EN + ES) for field rendering (~15 keys)

### Excluded (in other features)
- Admin definition management UI (F0 — already done)
- Backend storage/validation/enrichment (F1 — already done)
- Search/filter by custom fields in list views (F3)
- PDF/CSV export (F3)

## User Value

After this feature, users can fill in custom fields when creating/editing assets, requests, and incidents. Custom field values are visible on detail pages. The full end-to-end custom fields experience works for all users (admin, technician, employee).

## Acceptance Criteria

- [ ] `<CustomFieldsForm>` component renders fields based on definitions from API
- [ ] Text fields: standard text input
- [ ] Number fields: number input with step="any"
- [ ] Date fields: date picker consistent with app's existing date inputs
- [ ] Select fields: dropdown with admin-defined options
- [ ] Multi-select fields: checkboxes or multi-select control
- [ ] Boolean fields: checkbox with label
- [ ] Required fields show asterisk and block form submission if empty
- [ ] Custom fields appear after standard fields in create/edit forms
- [ ] Asset create/edit form includes custom fields section
- [ ] Request create/edit form includes custom fields section (respecting visible_to_employees)
- [ ] Incident create/edit form includes custom fields section
- [ ] Detail pages show "Custom Fields" section with label/value pairs
- [ ] Empty values display "—"
- [ ] Boolean values display "Yes"/"No"
- [ ] Multi-select values display as badges
- [ ] Inactive fields shown grayed out on detail pages
- [ ] Required fields without values show "Missing" indicator on detail pages
- [ ] TypeScript compiles clean (`npx tsc --noEmit`)

## Technical Scope

### Key Components
- `web/app/src/components/custom-fields/CustomFieldsForm.tsx` — reusable form component
- `web/app/src/components/custom-fields/CustomFieldsDisplay.tsx` — reusable detail display
- `web/app/src/components/custom-fields/fields/` — individual field type renderers
- `web/app/src/types/index.ts` — CustomField, CustomFieldDefinition interfaces
- `web/app/src/pages/technician/AssetFormPage.tsx` — integrate custom fields
- `web/app/src/pages/technician/AssetDetailPage.tsx` — add custom fields section
- `web/app/src/pages/technician/RequestDetailPage.tsx` — add custom fields section
- `web/app/src/pages/technician/IncidentDetail.tsx` — add custom fields section
- Request and incident create/edit pages — integrate custom fields
- `web/app/src/locales/en.ts` + `es.ts` — field rendering keys

## Notes

- The `<CustomFieldsForm>` component fetches definitions from `GET /custom-fields/definitions?entity_type=X` and renders accordingly. It outputs a `custom_fields_data` object that the parent form includes in the API call.
- The `<CustomFieldsDisplay>` component receives the enriched `custom_fields` array from the entity response and renders label/value pairs.
- Employee forms filter definitions by `visible_to_employees: true`.
