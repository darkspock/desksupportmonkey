# E31: Workflow Templates with Checklists

## Business Alignment

**Primary Objective:** Churn reduction / Operational efficiency
**Contribution:** Service desk teams currently have no structured way to track multi-step workflows (e.g., employee offboarding). Request types are hardcoded -- companies can't add their own. This epic makes request types dynamic and adds checklists per type.

**KPIs:**
- Reduce missed workflow steps (currently tracked informally in request descriptions)
- Improve resolution completeness for multi-step requests
- Enable accountability per checklist item (who did what, when)
- Allow companies to customize their request types

## Context

Today, request types are a hardcoded enum: incident, new_equipment, onboarding, repair, configuration, access_request. There's no way for a company to add their own types, and there's no structured way to define what steps need to happen for each type.

**The key insight:** Each request type IS a workflow. A WorkflowTemplate replaces the hardcoded enum and adds checklist capabilities.

**Example:** An employee offboarding request needs: disable email, wipe computer, collect badge, revoke VPN. Today this is just free text -- no tracking, no accountability.

**Design principle: KEEP IT SIMPLE.** Checklist items are just booleans. Like GitHub PR checklists.

## Design

### Core concept: WorkflowTemplate = Request Type

A **WorkflowTemplate** IS a request type. It replaces the hardcoded `RequestType` enum. Each template defines:
- **Identity:** name, description, icon (what the employee sees when picking a type)
- **Configuration:** subtypes, require_all_complete, is_active
- **Checklist items:** what steps get stamped onto every request of this type

**`service_requests.type`** becomes a FK to `workflow_templates.id`.

**Runtime:** When a request is created, the template's checklist items are copied as simple rows. Each item is just: title + assignee + done/not-done.

### Migration strategy

**Two-step approach:**

1. **Alembic migration (DDL only):** Create new tables (`workflow_templates`, `workflow_subtypes`, `checklist_item_definitions`, `request_checklist_items`). Add `workflow_template_id` column to `service_requests` (nullable).
2. **Separate Python script (data migration):** Run manually to create default templates for each existing company, then UPDATE `service_requests.workflow_template_id` based on old `type` values. After verification, a second Alembic migration makes `workflow_template_id` NOT NULL.

**Denormalization:** Keep `type` and `subtype` columns on `service_requests` as denormalized cache. When creating a new request, write the template name to `type`. This preserves history (if template is renamed, old requests keep the name they were created with) and keeps existing filters/reports/classification working.

## Domain Model

### WorkflowTemplate (the request type)

```
WorkflowTemplate
  id: str (ULID)
  company_id: str
  name: str                        # "Incidente", "Employee Offboarding"
  description: Optional[str]       # Shown to employees when picking type
  icon: Optional[str]              # Lucide icon name (e.g. "monitor", "user-plus")
  is_active: bool                  # Inactive templates don't show in picker
  require_all_complete: bool       # Block resolve until all checked?
  sort_order: int                  # Display order in picker
  created_at, updated_at

WorkflowSubtype (embedded in template)
  id: str (ULID)
  template_id: str
  name: str                        # "Hardware", "Software", etc.
  description: Optional[str]
  sort_order: int

ChecklistItemDefinition (embedded in template)
  id: str (ULID)
  template_id: str
  title: str                       # "Disable email account"
  description: Optional[str]       # Extra detail / instructions
  assignee_role: Optional[str]     # "technician", "admin"
  sort_order: int
  is_required: bool                # Must be completed (vs optional)
```

### RequestChecklistItem (runtime -- stamped per request)

```
RequestChecklistItem
  id: str (ULID)
  request_id: str
  require_all_complete: bool       # Copied from template at generation time
  title: str
  description: Optional[str]
  assignee_id: Optional[str]
  is_required: bool
  is_completed: bool
  completed_by: Optional[str]
  completed_at: Optional[datetime]
  sort_order: int
  created_at
```

## Bounded Context: `workflow_bc`

```
src/workflow_bc/
  template/
    domain/
      entities.py          # WorkflowTemplate, WorkflowSubtype, ChecklistItemDefinition
      repository.py        # WorkflowTemplateRepositoryInterface
      exceptions.py
    application/
      commands/
        create_template.py
        update_template.py
        delete_template.py
      queries/
        list_templates.py
        get_template.py
    infrastructure/
      models.py            # WorkflowTemplateModel, WorkflowSubtypeModel, ChecklistItemDefinitionModel
      repository.py
  checklist/
    domain/
      entities.py          # RequestChecklistItem
      repository.py        # ChecklistItemRepositoryInterface
      exceptions.py
    application/
      commands/
        generate_checklist.py      # Auto-create items from template
        toggle_item.py             # Check/uncheck an item
        assign_item.py             # Assign item to user
        add_item.py                # Ad-hoc item (no template)
        remove_item.py             # Remove ad-hoc item
      queries/
        list_items.py              # Items for a request
    infrastructure/
      models.py            # RequestChecklistItemModel
      repository.py
```

## Database

### Table: `workflow_templates`

| Column | Type | Notes |
|--------|------|-------|
| id | String(26) PK | ULID |
| company_id | String(26) FK | NOT NULL |
| name | String(255) | NOT NULL |
| description | Text | nullable |
| icon | String(50) | nullable. Lucide icon name. |
| is_active | Boolean | default true |
| require_all_complete | Boolean | default false |
| sort_order | Integer | default 0 |
| created_at | DateTime | |
| updated_at | DateTime | |

Unique: `(company_id, name)`

### Table: `workflow_subtypes`

| Column | Type | Notes |
|--------|------|-------|
| id | String(26) PK | ULID |
| template_id | String(26) FK | ON DELETE CASCADE |
| name | String(255) | NOT NULL |
| description | Text | nullable |
| sort_order | Integer | default 0 |

Unique: `(template_id, name)`

### Table: `checklist_item_definitions`

| Column | Type | Notes |
|--------|------|-------|
| id | String(26) PK | ULID |
| template_id | String(26) FK | ON DELETE CASCADE |
| title | String(255) | NOT NULL |
| description | Text | nullable |
| assignee_role | String(30) | nullable |
| sort_order | Integer | default 0 |
| is_required | Boolean | default true |

### Table: `request_checklist_items`

| Column | Type | Notes |
|--------|------|-------|
| id | String(26) PK | ULID |
| request_id | String(26) FK | NOT NULL, ON DELETE CASCADE |
| require_all_complete | Boolean | default false. Copied from template. |
| title | String(255) | NOT NULL |
| description | Text | nullable |
| assignee_id | String(26) | nullable |
| is_required | Boolean | default true |
| is_completed | Boolean | default false |
| completed_by | String(26) | nullable |
| completed_at | DateTime | nullable |
| sort_order | Integer | default 0 |
| created_at | DateTime | |

Index: `(request_id)`, `(assignee_id, is_completed)`

### Migration: `service_requests.type` change

The `service_requests` table currently has:
- `type`: String(30) -- stores enum values like "incident", "new_equipment"
- `subtype`: String(50) -- stores enum values like "hardware", "software"

**Migration steps:**
1. Add `workflow_template_id` column (String(26), nullable initially)
2. Add `workflow_subtype_id` column (String(26), nullable initially)
3. For each company: create default templates, map old type->template_id
4. UPDATE `service_requests` SET `workflow_template_id` = mapped template ID
5. Make `workflow_template_id` NOT NULL
6. Keep `type` and `subtype` columns as denormalized cache (for queries/filters)
7. Add FK index on `workflow_template_id`

## Default Templates (seeded per company)

| Name (en) | Name (es) | Icon | Subtypes |
|-----------|-----------|------|----------|
| Incident | Incidente | alert-circle | -- |
| New Equipment | Nuevo equipo | monitor | Computer, Mobile, Peripheral, Monitor, Software License |
| Onboarding | Onboarding | user-plus | -- |
| Repair | Reparacion | wrench | Hardware, Software, Network, Security, Other |
| Configuration | Configuracion | settings | Software Install, Account Setup, Permissions |
| Access Request | Solicitud de acceso | lock | System Access, Physical Access, VPN |

These are created:
1. On company creation (seed script)
2. Via separate Python migration script for existing companies

## Integration Points

### 1. Request creation

- Employee picks a WorkflowTemplate (not a hardcoded type)
- `CreateRequestCommand` receives `workflow_template_id` instead of `type` string
- After request is created, `GenerateChecklistCommandHandler` stamps checklist items
- Template lookup by ID (not by type+subtype anymore)

### 2. Request resolution guard

Before `ChangeRequestStatusCommand(RESOLVED)`:
- Fetch checklist items for request
- If any item has `require_all_complete=true` and `is_required=true` and `is_completed=false` -> HTTP 422

### 3. Request detail response

`GET /requests/{id}` includes:
```json
{
  "workflow_template_id": "...",
  "workflow_template_name": "Onboarding",
  "workflow_template_icon": "user-plus",
  "type": "onboarding",
  "subtype": null,
  "checklist": [...],
  "checklist_progress": { "total": 5, "completed": 2, "required_remaining": 3 }
}
```

### 4. Company creation

When a company is created, seed the 6 default workflow templates with their subtypes.

### 5. NewRequestPage

The type picker (screenshot) renders from `GET /api/v1/workflow-templates?active=true` instead of hardcoded types.

## API Endpoints

### Workflow Templates (admin)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/workflow-templates` | List templates (with subtypes + item count) |
| POST | `/api/v1/workflow-templates` | Create template with subtypes + items |
| GET | `/api/v1/workflow-templates/{id}` | Get template + subtypes + items |
| PUT | `/api/v1/workflow-templates/{id}` | Update template + subtypes + items |
| DELETE | `/api/v1/workflow-templates/{id}` | Delete template (fails if requests exist) |

### Request Checklist (technician+)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/requests/{id}/checklist` | List items |
| POST | `/api/v1/requests/{id}/checklist` | Add ad-hoc item |
| PATCH | `/api/v1/requests/{id}/checklist/{item_id}/toggle` | Check/uncheck |
| PATCH | `/api/v1/requests/{id}/checklist/{item_id}/assign` | Assign to user |
| DELETE | `/api/v1/requests/{id}/checklist/{item_id}` | Remove ad-hoc item |

## Frontend

### Admin: WorkflowTemplatesPage.tsx

- Card grid or table: icon, name, description, subtype count, checklist item count, active toggle
- Create/edit modal with:
  - Name, description, icon picker (lucide-react icons)
  - Subtypes list editor (add/remove/reorder)
  - Checklist items editor (add/remove/reorder)
  - require_all_complete toggle

### Employee: NewRequestPage.tsx

- Render type cards from `GET /api/v1/workflow-templates?active=true` instead of hardcoded types
- Each card shows icon, name, description from template
- Subtype picker from template's subtypes

### Technician: RequestDetailPage.tsx

- Checklist card with progress bar
- Toggle, assign, add/remove items
- Resolution warning if incomplete required items

## User Roles & Permissions

- **Admin:** Full CRUD on workflow templates
- **Technician:** Toggle, assign, add/remove checklist items on requests
- **Employee:** View-only checklist on their own requests; pick template when creating request

## Files Impacted (Existing)

| File | Change |
|------|--------|
| `src/request_bc/request/domain/entities.py` | Add `workflow_template_id`, keep `type` as denormalized |
| `src/request_bc/request/domain/enums.py` | Keep `RequestType` for backwards compat, deprecate |
| `src/request_bc/request/infrastructure/models.py` | Add `workflow_template_id` column |
| `src/request_bc/request/application/commands/create_request.py` | Accept template_id instead of type enum |
| `adapters/http/api/requests/routers.py` | Hook checklist generation, resolution guard, template lookup |
| `adapters/http/api/requests/schemas.py` | Add checklist + template fields to responses |
| `web/app/src/pages/employee/NewRequestPage.tsx` | Render from templates API |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Checklist card |
| `web/app/src/pages/technician/RequestQueuePage.tsx` | Show template name instead of enum |
| `web/app/src/types/index.ts` | New types |
| `web/app/src/router.tsx` | Admin route |
| `web/app/src/components/layout/Sidebar.tsx` | Admin nav link |
| `web/app/src/locales/en.ts` + `es.ts` | i18n |
| `app.py` | Register routers |
| `scripts/seed_demo_data.py` | Seed templates on company creation |
| Company creation flow | Seed default templates |

## Implementation Phases

### Phase 1: WorkflowTemplate as request type (backend)

1. `workflow_bc` domain entities (WorkflowTemplate, WorkflowSubtype, ChecklistItemDefinition, RequestChecklistItem)
2. Repository interfaces + SQLAlchemy models
3. Alembic migration: new tables + seed defaults for existing companies + alter service_requests
4. Template CRUD commands/queries
5. Checklist commands (generate, toggle, assign, add, remove)
6. HTTP routes for templates and checklist
7. Hook into request creation (template_id instead of type enum)
8. Hook into request resolution (checklist guard)
9. Seed templates on company creation
10. Unit + integration tests

### Phase 2: Frontend

1. Install lucide-react
2. Admin WorkflowTemplatesPage.tsx
3. Update NewRequestPage.tsx to use templates API
4. RequestDetailPage.tsx checklist card
5. Update RequestQueuePage to show template name
6. TypeScript types, i18n, router, sidebar

### Phase 3: Polish (optional)

1. "My checklist items" page/widget
2. Notifications when item is assigned to you
3. Notifications when all items complete

## Resolved Design Decisions

| Decision | Answer |
|----------|--------|
| Resolution guard data | Store `require_all_complete` on `request_checklist_items` |
| Unique constraint for name | Application-level check in handler |
| Un-toggle items | Yes, freely (any technician+) |
| Audit trail | Yes, in Phase 1 |
| Icon library | lucide-react |
| `service_requests.type` | FK to `workflow_templates.id`, keep old `type` as denormalized cache |
| Subtypes | Dynamic, defined per template |
| Migration approach | Alembic for DDL only, separate Python script for data migration |

## Verification

1. `make test` -- all unit tests pass
2. `make test-integration` -- integration tests pass
3. `cd web/app && npx tsc --noEmit` -- TypeScript clean
4. Migration: existing requests correctly linked to new templates
5. NewRequestPage renders from API instead of hardcoded types
6. Admin can create custom request types with checklists

## Out of Scope

- Checklist item dependencies (item B blocked until A is done)
- Checklist item due dates
- Template versioning
- Conditional checklist items (if X then show Y)
- Bulk operations on checklist items
- Custom status machines per template (all use same state machine)
