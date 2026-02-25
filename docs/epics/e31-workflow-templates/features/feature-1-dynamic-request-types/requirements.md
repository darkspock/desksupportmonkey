# Feature 1: Dynamic Request Types

**Parent Epic:** [../../requirement.md](../../requirement.md)
**Feature #:** 1
**Dependencies:** Feature 0
**Complexity:** M

## Scope

### Included
- **NewRequestPage.tsx**: Replace hardcoded `TYPE_CONFIG` with API call to `GET /api/v1/workflow-templates?active=true`. Render type cards from template data (name, description, icon). Subtype picker from template's subtypes.
- **Request creation flow**: `CreateRequestCommand` receives `workflow_template_id`. Write template name to `service_requests.type` as denormalized cache. Write subtype name to `service_requests.subtype`.
- **Request detail response**: Enrich `GET /requests/{id}` with `workflow_template_id`, `workflow_template_name`, `workflow_template_icon` fields.
- **Request list response**: Include `workflow_template_name` and `workflow_template_icon` in list item response.
- **Default templates complete**: Ensure all 6 default templates exist with correct icons and subtypes:
  - Incident (icon: alert-circle)
  - New Equipment (icon: monitor) — subtypes: Computer, Mobile, Peripheral, Monitor, Software License
  - Onboarding (icon: user-plus)
  - Repair (icon: wrench) — subtypes: Hardware, Software, Network, Security, Other
  - Configuration (icon: settings) — subtypes: Software Install, Account Setup, Permissions
  - Access Request (icon: lock) — subtypes: System Access, Physical Access, VPN

### Excluded (in other features)
- Checklist card on RequestDetailPage (Feature 2 — already done)
- RequestQueuePage template display (Feature 3)
- lucide-react installation (Feature 3)
- Data migration for existing requests (Feature 4)

## User Value

Employees pick a request type from a dynamic list configured by their company admin — not from a hardcoded set. Companies can add their own request types with descriptions and icons. Request detail shows which template was used.

## Acceptance Criteria

- [ ] NewRequestPage loads types from `GET /api/v1/workflow-templates?active=true`
- [ ] Type cards show template name, description, and icon
- [ ] Subtype picker renders from template's subtypes (if any)
- [ ] Request creation sends `workflow_template_id` (and optionally `workflow_subtype_id`)
- [ ] `service_requests.type` populated with template name (denormalized)
- [ ] `service_requests.subtype` populated with subtype name (denormalized)
- [ ] `GET /requests/{id}` response includes `workflow_template_id`, `workflow_template_name`, `workflow_template_icon`
- [ ] Request list response includes template name
- [ ] Default templates updated: 6 types, with icons and subtypes
- [ ] Backward compatible: existing requests with old type values still display correctly
- [ ] Unit tests for updated creation flow
- [ ] TypeScript compiles clean

## Technical Scope

### Entities (used from dependencies)
- WorkflowTemplate (Feature 0)
- WorkflowSubtype (Feature 0)

### Key Components
- `web/app/src/pages/employee/NewRequestPage.tsx` — Major rewrite of type picker
- `adapters/http/api/requests/routers.py` — Request creation: resolve template, write denormalized type/subtype
- `adapters/http/api/requests/schemas.py` — Add template fields to RequestResponse and RequestListItemResponse
- `src/company_bc/company/application/commands/create_company.py` — Update DEFAULT_WORKFLOW_TEMPLATES with 6 types, icons, subtypes

## Notes

- The old `TYPE_CONFIG` in NewRequestPage has hardcoded SVG icons. These will be replaced by lucide icon names from templates. If lucide-react is not yet installed (Feature 3), render a fallback icon or use the icon name as text.
- Keep `service_requests.type` and `service_requests.subtype` columns as denormalized cache. When a request is created, copy template.name → type and subtype.name → subtype. This preserves history if templates are renamed.
