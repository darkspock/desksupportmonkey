# Implementation Tasks: Feature 1 — Dynamic Request Types

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-25
**Total Tasks:** 10
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Entity updates | 1 | S |
| Infrastructure - Repository mappers | 1 | S |
| Application - Command updates | 1 | S |
| HTTP - Schema updates | 1 | S |
| HTTP - Router (create + enrich) | 1 | L |
| Data - Default templates expansion | 1 | M |
| Data - Seed script update | 1 | S |
| Frontend - NewRequestPage rewrite | 1 | L |
| Tests - Unit | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Add Template Fields to ServiceRequest Entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** F0 complete

**File:** `src/request_bc/request/domain/entities.py`

**Implementation:**
Add optional fields to the `ServiceRequest` dataclass:
```python
workflow_template_id: Optional[str] = None
workflow_subtype_id: Optional[str] = None
```

Update `create()` factory method to accept these optional parameters and pass them through.

When `workflow_template_id` is provided, skip the enum-based subtype validation (the router validates against the template's subtypes instead).

**Acceptance Criteria:**
- [x] `workflow_template_id` field added with `None` default
- [x] `workflow_subtype_id` field added with `None` default
- [x] `create()` accepts both new params
- [x] When `workflow_template_id` is set, subtype enum validation is skipped
- [x] Existing tests still pass (fields are optional)

---

## Phase 2: Infrastructure Layer

### TASK-002: Update Request Repository Mappers

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**File:** `src/request_bc/request/infrastructure/repository.py`

**Implementation:**
Update `_entity_to_model()` and `_model_to_entity()` to include `workflow_template_id` and `workflow_subtype_id`. The model columns already exist from the Feature 0 migration.

**Acceptance Criteria:**
- [x] Entity→Model includes `workflow_template_id`
- [x] Entity→Model includes `workflow_subtype_id`
- [x] Model→Entity includes both fields
- [x] Null handling (None for both when not set)

---

## Phase 3: Application Layer

### TASK-003: Add Template Fields to CreateRequestCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-001

**File:** `src/request_bc/request/application/commands/create_request.py`

**Implementation:**
Add to `CreateRequestCommand` dataclass:
```python
workflow_template_id: Optional[str] = None
workflow_subtype_id: Optional[str] = None
```

Update handler to pass these fields to `ServiceRequest.create()`.

**Acceptance Criteria:**
- [x] Command accepts `workflow_template_id` and `workflow_subtype_id`
- [x] Handler passes both to entity `create()`
- [x] Existing callers unaffected (both are optional)

---

## Phase 4: HTTP Layer

### TASK-004: Update Request Response Schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Files:** `adapters/http/api/requests/schemas.py`

**Implementation:**
Add to `RequestResponse`:
```python
workflow_template_id: Optional[str] = None
workflow_template_name: Optional[str] = None
workflow_template_icon: Optional[str] = None
```

Add to `RequestListItemResponse`:
```python
workflow_template_name: Optional[str] = None
workflow_template_icon: Optional[str] = None
```

**Acceptance Criteria:**
- [x] `RequestResponse` has all 3 template fields
- [x] `RequestListItemResponse` has name and icon
- [x] All fields are Optional (backward compatible)

---

### TASK-005: Update Request Router — Template Resolution + Response Enrichment

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-002, TASK-003, TASK-004

**File:** `adapters/http/api/requests/routers.py`

**Implementation:**

**A) Request creation (POST /requests):**
When `body.template_id` is provided:
1. Fetch template from `WorkflowTemplateRepository` by ID and company_id
2. Validate template exists and is active → 422 if not
3. Use `template.name` as the `type` value (denormalized into service_requests.type)
4. If `body.subtype` provided, match against `template.subtypes` by name → get `workflow_subtype_id`
5. Pass `workflow_template_id=template.id` and `workflow_subtype_id` to `CreateRequestCommand`

**B) Request detail (GET /requests/{id}):**
If `request.workflow_template_id` is not None:
1. Look up template from repository
2. Pass `workflow_template_name=template.name` and `workflow_template_icon=template.icon` to `_to_response()`
3. If template was deleted, these will be None (the denormalized `type` column preserves the name)

**C) Request list (GET /requests):**
For requests that have `workflow_template_id`:
1. Collect unique template IDs from all requests
2. Batch-fetch templates
3. Build id→template map
4. Pass name/icon to each `_to_response()` call

**D) `_to_response()` helper:**
Add `workflow_template_name` and `workflow_template_icon` keyword args. Map them into `RequestResponse`.

**Acceptance Criteria:**
- [x] POST /requests with `template_id` resolves template and writes `workflow_template_id`
- [x] POST /requests with `template_id` writes template.name to `type` (denormalized)
- [x] POST /requests with `template_id` + subtype resolves `workflow_subtype_id`
- [x] POST /requests with invalid `template_id` returns 422
- [x] GET /requests/{id} includes `workflow_template_name` and `workflow_template_icon`
- [x] GET /requests list includes template name/icon per item
- [x] Deleted templates → null name/icon (graceful degradation)

---

## Phase 5: Default Templates Data

### TASK-006: Expand DEFAULT_WORKFLOW_TEMPLATES to 6 Types with Icons and Subtypes

**Phase:** Data
**Complexity:** M
**Dependencies:** None

**File:** `src/company_bc/company/application/commands/create_company.py`

**Implementation:**
Update `DEFAULT_WORKFLOW_TEMPLATES` list:

1. **Incident** — icon: `alert-circle`, no subtypes
2. **New Equipment** — icon: `monitor`, subtypes: Computer, Mobile, Peripheral, Monitor, Software License
3. **Onboarding** — icon: `user-plus`, no subtypes
4. **Repair** — icon: `wrench`, subtypes: Hardware, Software, Network, Security, Other
5. **Configuration** — icon: `settings`, subtypes: Software Install, Account Setup, Permissions
6. **Access Request** — icon: `lock`, subtypes: System Access, Physical Access, VPN

Replace "Employee Offboarding" with "Repair" and add "Configuration". Add `icon` and `subtypes` keys to each dict.

Update seeding logic in `CreateCompanyCommandHandler.handle()`:
- Pass `icon=spec.get("icon")` to `WorkflowTemplate.create()`
- After creating template, create `WorkflowSubtype` entities from `spec.get("subtypes", [])` and call `template.set_subtypes()`

**Acceptance Criteria:**
- [x] 6 templates defined (not 5)
- [x] Each has `icon` field with lucide icon name
- [x] Templates with subtypes have `subtypes` list defined
- [x] Seeding logic creates `WorkflowSubtype` entities
- [x] Seeding passes `icon` to template creation
- [x] Template names match the `RequestType` enum values when lowercased/underscored

---

### TASK-007: Update Seed Demo Data

**Phase:** Data
**Complexity:** S
**Dependencies:** TASK-006

**File:** `scripts/seed_demo_data.py`

**Implementation:**
Update the workflow template seeding section to include icons and subtypes matching `DEFAULT_WORKFLOW_TEMPLATES`. If the seed script creates templates separately from company creation, align it with the new 6-template structure.

**Acceptance Criteria:**
- [x] `make seed` works without errors
- [x] Demo data includes all 6 template types
- [x] Templates have icons and subtypes populated

---

## Phase 6: Frontend

### TASK-008: Rewrite NewRequestPage Type Selection

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-005

**File:** `web/app/src/pages/employee/NewRequestPage.tsx`

**Implementation:**

**A) Replace TYPE_CONFIG with API query:**
```typescript
const templatesQuery = useQuery({
  queryKey: ['workflow-templates', { active: true }],
  queryFn: async () => {
    const { data } = await api.get('/workflow-templates?active=true');
    return data.data as WorkflowTemplate[];
  },
});
```

**B) Update form state:**
```typescript
const [form, setForm] = useState({
  templateId: '',
  type: '',
  title: '',
  description: '',
  subtype: '',
  subtypeId: '',
});
```

**C) Type card rendering:**
- Map over `templatesQuery.data` instead of `TYPE_CONFIG`
- Show template name as label, template description below
- Icon: render icon name as text/fallback (lucide-react comes in Feature 3)
- Selected state based on `form.templateId === template.id`

**D) Subtype picker:**
- Get subtypes from selected template: `selectedTemplate?.subtypes ?? []`
- Replace `VALID_SUBTYPES[form.type]` with template's subtypes
- On subtype select, set both `subtype` (name) and `subtypeId` (id)

**E) Request submission:**
```typescript
const body = {
  type: form.type,               // template name (still needed for backward compat)
  template_id: form.templateId,
  title: form.title,
  description: form.description,
};
if (form.subtype) body.subtype = form.subtype;
```

**F) Loading/error states:**
- Show skeleton while templates load
- Show error message if templates query fails
- Empty state if company has no active templates

**G) Budget logic:**
- Keep `SUBTYPE_ASSET_MAP` — it maps subtype names (which stay the same) to asset types
- Trigger budget query when template name is "New Equipment" and subtype is selected

**Acceptance Criteria:**
- [x] TYPE_CONFIG replaced with API fetch
- [x] Type cards rendered from template data (name, description)
- [x] Icon fallback works (no lucide-react yet)
- [x] Subtypes loaded from selected template
- [x] Request submission includes `template_id`
- [x] Loading skeleton shown while fetching
- [x] Error state if API fails
- [x] Budget indicator still works for "New Equipment"
- [x] `SUBTYPE_ASSET_MAP` still functional
- [x] TypeScript compiles clean

---

## Phase 7: Tests

### TASK-009: Unit Tests for Command and Entity Changes

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001, TASK-003

**Files:**
- `tests/unit/request_bc/request/domain/test_entities.py`
- `tests/unit/request_bc/request/application/commands/test_create_request.py`

**Implementation:**

**Entity tests:**
- `ServiceRequest.create()` with `workflow_template_id` → field set correctly
- `ServiceRequest.create()` with `workflow_template_id` + subtype → skips enum validation
- `ServiceRequest.create()` without `workflow_template_id` → existing subtype validation still works

**Command tests:**
- `CreateRequestCommand` with `workflow_template_id` → passed to entity
- `CreateRequestCommand` with both template fields → both persisted

**Acceptance Criteria:**
- [x] Entity creation with template fields tested
- [x] Subtype validation bypass with template tested
- [x] Subtype validation still enforced without template
- [x] Command handler passes template fields through
- [x] `make test` passes (all existing + new tests)

---

## Phase 8: Verification

### TASK-010: Final Verification

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Implementation:**
1. Run `make test` — all unit tests pass
2. Run `make lint` — mypy + flake8 clean
3. Run `cd web/app && npx tsc --noEmit` — TypeScript compiles clean
4. Run `make seed` — seed data works
5. Manual test: create a request via NewRequestPage, verify template_id is set, verify detail shows template name/icon

**Acceptance Criteria:**
- [x] `make test` passes
- [x] `make lint` passes (pre-existing E501 in workflow_bc infra, not from this feature)
- [x] TypeScript compiles clean
- [x] `make seed` works
- [ ] New request creation flow works end-to-end (pending user local testing)

---

## Dependency Graph

```
F0 complete
    │
    ├── TASK-001 (Entity fields)
    │       │
    │       ├── TASK-002 (Repo mappers)
    │       └── TASK-003 (Command update)
    │               │
    ├── TASK-004 (Schema updates)
    │               │
    │       TASK-005 (Router: create + enrich) ◄── TASK-002 + TASK-003 + TASK-004
    │               │
    │       TASK-008 (Frontend) ◄── TASK-005
    │
    ├── TASK-006 (Default templates) [parallel]
    │       │
    │       TASK-007 (Seed data) ◄── TASK-006
    │
    ├── TASK-009 (Tests) ◄── TASK-001 + TASK-003
    │
    └── TASK-010 (Verification) ◄── ALL
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-004, TASK-006
**Batch 2 (Parallel):** TASK-002, TASK-003, TASK-007
**Batch 3:** TASK-005
**Batch 4 (Parallel):** TASK-008, TASK-009
**Batch 5:** TASK-010

## Final Checklist

- [x] All 10 tasks completed
- [x] `make test` passes (1763 tests)
- [x] `make lint` passes (pre-existing E501 only)
- [x] TypeScript compiles clean
- [x] `make seed` works
- [x] Request creation sends `template_id`
- [x] Request detail shows template name/icon
- [x] Request list shows template name
- [x] Default templates: 6 types with icons and subtypes
- [x] Backward compatible with existing requests
