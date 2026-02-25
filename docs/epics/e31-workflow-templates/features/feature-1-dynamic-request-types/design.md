# Solution Design: Feature 1 — Dynamic Request Types

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-25
**Bounded Contexts:** `request_bc`, `workflow_bc`, `company_bc`

## Summary

Replace the hardcoded `RequestType` enum-driven request creation flow with a dynamic, template-driven flow. The frontend fetches active workflow templates from the API and renders type cards from that data. The backend writes `workflow_template_id` and `workflow_subtype_id` to `service_requests` on creation, with the template name and subtype name denormalized into the existing `type` and `subtype` text columns. Default templates are expanded from 5 to 6 with icons and subtypes.

## Architecture Decision

**Approach: Additive, backward-compatible transition.**

The `RequestType` enum and `VALID_SUBTYPES` remain in the codebase — they're still used by the priority scorer, auto-assignment logic, and existing requests. The key change is that the **frontend** stops using them as the source of truth for type selection and instead uses the workflow templates API.

When a request is created with a `template_id`:
1. The router resolves the template, writes `workflow_template_id` on the request
2. The template's name is written to `service_requests.type` (denormalized)
3. The subtype name (if any) is written to `service_requests.subtype` (denormalized)
4. The enum-based validation in `ServiceRequest.create()` still works because default template names map 1:1 to enum values

This avoids a risky migration of the enum system while enabling dynamic templates for new companies and custom types.

**Why not remove the enum now?** The enum is deeply coupled to priority scoring, auto-assignment, approval logic, and 50+ existing tests. Removing it is a separate, larger refactor. For now, the enum stays as a compatibility layer.

## Existing Code Analysis

| Component | Location | Modifications Needed |
|-----------|----------|---------------------|
| NewRequestPage.tsx | `web/app/src/pages/employee/NewRequestPage.tsx` | Replace `TYPE_CONFIG` with API query; replace `VALID_SUBTYPES` with template subtypes |
| Request schemas | `adapters/http/api/requests/schemas.py` | Add `workflow_template_id`, `workflow_template_name`, `workflow_template_icon` to responses |
| Request router | `adapters/http/api/requests/routers.py` | Resolve template on create, write template fields to request; enrich GET responses |
| `_to_response` helper | `adapters/http/api/requests/routers.py:201` | Add template fields to response mapping |
| ServiceRequest entity | `src/request_bc/request/domain/entities.py` | Add `workflow_template_id`, `workflow_subtype_id` fields |
| ServiceRequest model | `src/request_bc/request/infrastructure/models.py` | Already has `workflow_template_id` and `workflow_subtype_id` columns |
| Request repository | `src/request_bc/request/infrastructure/repository.py` | Update entity↔model mapping |
| CreateRequestCommand | `src/request_bc/request/application/commands/create_request.py` | Add `workflow_template_id`, `workflow_subtype_id` params |
| DEFAULT_WORKFLOW_TEMPLATES | `src/company_bc/company/application/commands/create_company.py` | Add Repair + Configuration templates, add icons and subtypes to all 6 |
| TypeScript types | `web/app/src/types/index.ts` | Already has `WorkflowTemplate` type from Feature 0 |
| Workflow templates router | `adapters/http/api/workflow_templates/routers.py` | No changes needed — already supports `?active=true` filter |

## Implementation Plan

### 1. Domain Layer

#### Entity Changes (modify)

**ServiceRequest** (`src/request_bc/request/domain/entities.py`):
```python
# Add to dataclass
workflow_template_id: Optional[str] = None
workflow_subtype_id: Optional[str] = None

# Update create() to accept these optional fields
```

No new entities or value objects needed.

#### Subtype Validation Change

Currently `ServiceRequest.create()` validates subtypes against the hardcoded `VALID_SUBTYPES` enum. When `workflow_template_id` is provided, the router will have already validated the subtype against the template's subtypes, so the entity's enum-based validation should be relaxed for template-based requests.

**Strategy:** When `workflow_template_id` is provided, skip the enum-based subtype validation in `ServiceRequest.create()`. The router handles validation against the template.

### 2. Application Layer

#### Command Changes (modify)

**CreateRequestCommand** (`src/request_bc/request/application/commands/create_request.py`):
```python
@dataclass
class CreateRequestCommand(Command):
    # ... existing fields ...
    workflow_template_id: Optional[str] = None
    workflow_subtype_id: Optional[str] = None
```

Handler passes these through to `ServiceRequest.create()`.

### 3. Infrastructure Layer

#### Repository Changes (modify)

**RequestRepository** — update `_entity_to_model()` and `_model_to_entity()` to include `workflow_template_id` and `workflow_subtype_id`. The model columns already exist (from Feature 0 migration).

No new migrations needed.

### 4. HTTP Layer

#### Schema Changes (modify)

**RequestResponse** and **RequestListItemResponse** (`adapters/http/api/requests/schemas.py`):
```python
class RequestResponse(BaseModel):
    # ... existing fields ...
    workflow_template_id: Optional[str] = None
    workflow_template_name: Optional[str] = None
    workflow_template_icon: Optional[str] = None

class RequestListItemResponse(BaseModel):
    # ... existing fields ...
    workflow_template_name: Optional[str] = None
    workflow_template_icon: Optional[str] = None
```

#### Router Changes (modify)

**Request creation** (`adapters/http/api/requests/routers.py`):

When `body.template_id` is provided:
1. Fetch the template from `WorkflowTemplateRepository`
2. If template not found or not active → 422
3. Resolve subtype: if `body.subtype` provided, match against template's subtypes by name → get `workflow_subtype_id`
4. Pass `workflow_template_id` and `workflow_subtype_id` to `CreateRequestCommand`
5. Use template name as the `type` field value (denormalized)
6. Use subtype name as the `subtype` field value (denormalized)

**Request detail/list responses:**
- Inject `WorkflowTemplateRepository` via dependency
- For single GET: look up template by `request.workflow_template_id` if present → include name and icon in response
- For list: batch-fetch templates for all requests with `workflow_template_id` → include name/icon in each response item
- If template was deleted, fields are null (the denormalized `type` column preserves the historical name)

#### `_to_response` helper update:
```python
def _to_response(
    request, ...,
    workflow_template_name: str | None = None,
    workflow_template_icon: str | None = None,
) -> RequestResponse:
    return RequestResponse(
        # ... existing fields ...
        workflow_template_id=request.workflow_template_id,
        workflow_template_name=workflow_template_name,
        workflow_template_icon=workflow_template_icon,
    )
```

### 5. Default Templates Update

**DEFAULT_WORKFLOW_TEMPLATES** (`src/company_bc/company/application/commands/create_company.py`):

Expand from 5 templates to 6. Add `icon` and `subtypes` to each:

| Template | Icon | Subtypes |
|----------|------|----------|
| Incident | alert-circle | — |
| New Equipment | monitor | Computer, Mobile, Peripheral, Monitor, Software License |
| Onboarding | user-plus | — |
| Repair | wrench | Hardware, Software, Network, Security, Other |
| Configuration | settings | Software Install, Account Setup, Permissions |
| Access Request | lock | System Access, Physical Access, VPN |

"Employee Offboarding" is renamed/replaced with "Repair" and "Configuration" is added. The 6 templates match the 6 values in the `RequestType` enum.

**Seeding logic** must also create `WorkflowSubtype` entities for each template's subtypes.

### 6. Frontend Changes

#### NewRequestPage.tsx (major rewrite of type selection)

**Replace `TYPE_CONFIG` with API query:**
```typescript
const templatesQuery = useQuery({
  queryKey: ['workflow-templates', { active: true }],
  queryFn: async () => {
    const { data } = await api.get('/workflow-templates?active=true');
    return data.data as WorkflowTemplate[];
  },
});
```

**Form state changes:**
```typescript
const [form, setForm] = useState({
  templateId: '',      // workflow_template_id
  type: '',            // denormalized from template.name
  title: '',
  description: '',
  subtype: '',         // denormalized from selected subtype.name
  subtypeId: '',       // workflow_subtype_id
});
```

**Type cards render from templates:**
- Card shows template name (instead of i18n enum key)
- Card shows template description
- Icon rendered as text/fallback (lucide-react not installed until Feature 3)

**Subtypes from selected template:**
- When user selects a template, subtypes come from `template.subtypes[]`
- Replace `VALID_SUBTYPES[form.type]` with `selectedTemplate?.subtypes ?? []`

**Request submission:**
```typescript
const body = {
  type: selectedTemplate.name,           // denormalized name
  template_id: selectedTemplate.id,
  title: form.title,
  description: form.description,
  subtype: selectedSubtype?.name,        // denormalized name
};
```

**Budget logic:**
- The `SUBTYPE_ASSET_MAP` currently maps subtype enum values to asset types
- This stays as-is for now — the subtype names from templates match the same values
- When the template name is "New Equipment" and subtype is selected, budget query still works

**Backward compatibility:**
- If templates API returns empty (edge case), show error/fallback
- Existing `RequestType` type still used in TypeScript for display/routing elsewhere

### 7. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/request_bc/request/domain/entities.py` | Add fields | `workflow_template_id`, `workflow_subtype_id` |
| `src/request_bc/request/infrastructure/repository.py` | Update mapping | Include new fields in entity↔model |
| `src/request_bc/request/application/commands/create_request.py` | Add params | `workflow_template_id`, `workflow_subtype_id` |
| `adapters/http/api/requests/schemas.py` | Add fields | Template fields to response schemas |
| `adapters/http/api/requests/routers.py` | Template resolution | Create + detail + list enrichment |
| `src/company_bc/company/application/commands/create_company.py` | Expand data | 6 templates with icons and subtypes |
| `web/app/src/pages/employee/NewRequestPage.tsx` | Major rewrite | Dynamic type selection from API |
| `web/app/src/types/index.ts` | Verify types | Ensure WorkflowTemplate type includes subtypes |
| `scripts/seed_demo_data.py` | Update seeds | Update template seeds to include icons and subtypes |

#### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| NewRequestPage sends `template_id` | Backend already accepts it | None |
| Request responses get new optional fields | Additive, backward compatible | None |
| Default templates change from 5→6 | Only affects new companies | Existing companies keep their templates |

## Database Schema

No new migrations needed. The `workflow_template_id` and `workflow_subtype_id` columns already exist on `service_requests` (from Feature 0 migration). The `workflow_templates` and `workflow_subtypes` tables already exist.

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | `CreateRequestCommand` with `workflow_template_id` | High |
| Unit | `ServiceRequest.create()` with template fields | High |
| Unit | Updated `DEFAULT_WORKFLOW_TEMPLATES` seeding with subtypes | High |
| Unit | Request repository entity↔model mapping includes template fields | Medium |
| Integration | POST /requests with template_id → workflow_template_id persisted | High |
| Integration | GET /requests/{id} returns template name and icon | High |
| Integration | GET /requests returns template name in list items | Medium |
| TypeScript | `npx tsc --noEmit` compiles clean | High |

## Implementation Order

1. [ ] Domain: Add `workflow_template_id`, `workflow_subtype_id` to ServiceRequest entity
2. [ ] Infrastructure: Update repository entity↔model mapping
3. [ ] Application: Add template fields to CreateRequestCommand + handler
4. [ ] HTTP schemas: Add template fields to RequestResponse, RequestListItemResponse
5. [ ] HTTP router: Template resolution on create (lookup template, write fields)
6. [ ] HTTP router: Enrich GET detail/list responses with template name/icon
7. [ ] Default templates: Expand to 6 with icons and subtypes
8. [ ] Seed data: Update seed script to include icons and subtypes
9. [ ] Frontend: Rewrite NewRequestPage type selection to use templates API
10. [ ] Unit tests for command and entity changes
11. [ ] TypeScript compile check

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Existing tests break from entity field additions | Low | Medium | Fields are Optional with defaults; existing tests don't set them |
| Priority scorer depends on RequestType enum | Low | Low | Template name maps to enum value; scorer still works |
| Auto-assign depends on request type | Low | Low | Type field still populated with enum-compatible name |
| NewRequestPage breaks if templates API fails | Medium | High | Add loading/error states; consider fallback to hardcoded types |
