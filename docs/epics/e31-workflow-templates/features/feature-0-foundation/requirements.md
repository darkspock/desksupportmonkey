# Feature 0: Workflow Templates Foundation

**Parent Epic:** [../../requirement.md](../../requirement.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** L

## Scope

### Included
- `workflow_bc` bounded context: template + checklist subdomains
- Domain entities: WorkflowTemplate, WorkflowSubtype, ChecklistItemDefinition, RequestChecklistItem
- Repository interfaces + SQLAlchemy models (Mapped style)
- Alembic migration: 4 new tables (workflow_templates, workflow_subtypes, checklist_item_definitions, request_checklist_items) + 2 columns on service_requests (workflow_template_id, workflow_subtype_id)
- Template CRUD: CreateTemplateCommand, UpdateTemplateCommand, DeleteTemplateCommand
- Template queries: ListTemplatesQuery, GetTemplateQuery
- Checklist commands: GenerateChecklistCommand, ToggleItemCommand, AssignItemCommand, AddItemCommand, RemoveItemCommand
- Checklist queries: ListItemsQuery
- HTTP routes: 5 template endpoints + 5 checklist endpoints
- Admin WorkflowTemplatesPage.tsx (CRUD with subtypes + checklist items editor)
- TypeScript types, i18n keys (en + es), router registration, sidebar nav link
- Register routers in app.py
- Seed data in seed_demo_data.py
- Default templates seeded on company creation
- Unit tests for all commands, queries, and domain entities

### Excluded (in other features)
- NewRequestPage integration (Feature 1)
- Request detail response enrichment (Feature 1)
- RequestQueuePage template display (Feature 3)
- lucide-react installation (Feature 3)
- Data migration for existing requests (Feature 4)

## User Value

Admin can create, edit, and delete workflow templates with subtypes and checklist item definitions. Templates are automatically created for new companies. This is the configuration layer that enables all other features.

## Acceptance Criteria

- [x] workflow_bc domain entities with factory methods and validation
- [x] Repository interfaces + SQLAlchemy infrastructure (Mapped style)
- [x] Alembic migration creates 4 tables + 2 FK columns on service_requests
- [x] Template CRUD commands with company scoping and name uniqueness
- [x] Checklist commands (generate, toggle, assign, add, remove)
- [x] 5 template API endpoints (GET list, POST, GET one, PUT, DELETE)
- [x] 5 checklist API endpoints (GET list, POST, PATCH toggle, PATCH assign, DELETE)
- [x] Admin WorkflowTemplatesPage with table, create/edit modal, delete confirmation
- [x] TypeScript types for WorkflowTemplate, ChecklistItemDefinition, RequestChecklistItem
- [x] i18n keys in en.ts and es.ts
- [x] Route and sidebar nav link registered
- [x] Default templates seeded on company creation (CreateCompanyCommandHandler)
- [x] Unit tests pass (42 workflow tests)
- [x] TypeScript compiles clean

## Technical Scope

### Entities (owned by this feature)
- WorkflowTemplate (workflow_bc/template/domain)
- WorkflowSubtype (workflow_bc/template/domain)
- ChecklistItemDefinition (workflow_bc/template/domain)
- RequestChecklistItem (workflow_bc/checklist/domain)

### Key Components
- `src/workflow_bc/` — Full bounded context
- `adapters/http/api/workflow_templates/` — Template router + schemas
- `adapters/http/api/checklist/` — Checklist router + schemas
- `web/app/src/pages/admin/WorkflowTemplatesPage.tsx`
- `alembic/versions/z4c5d6e7f8g9_create_workflow_tables.py`
