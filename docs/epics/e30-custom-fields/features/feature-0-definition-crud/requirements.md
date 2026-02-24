# Feature 0: Definition CRUD

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** M

## Scope

### Included
- `custom_field_bc` bounded context: domain entities, enums, exceptions, repository interface
- `CustomFieldDefinition` entity with all fields (including `visible_to_employees`)
- Infrastructure: SQLAlchemy model, Alembic migration (`custom_field_definitions` table)
- Repository implementation
- Application layer: commands (create, update, delete, deactivate, activate, reorder) + queries (list, get by id)
- HTTP endpoints: all 8 definition endpoints (list, get, create, update, delete, deactivate, activate, reorder)
- Plan gating: Enterprise required for all definition endpoints
- Frontend: Admin page under Settings > Custom Fields with tabs (Assets/Requests/Incidents), create/edit modal, reorder, deactivate/delete
- i18n keys (EN + ES) for definition management
- Sidebar + router integration
- Unit tests: entity validation (slug generation, max 20, type constraints, options validation)
- Unit tests: all command/query handlers
- Integration tests: definition CRUD endpoints, plan gating (402)

### Excluded (in other features)
- JSONB column on target entities (F1)
- Custom field values storage/retrieval (F1)
- Entity endpoint modifications (F1)
- Frontend dynamic field rendering in forms (F2)
- Custom field display on detail pages (F2)
- Search/filter by custom fields (F3)
- Export integration (F3)

## User Value

Admin can define, configure, and manage custom field schemas for their organization. After this feature, the admin has a complete management interface for field definitions — the "what fields exist" part. Values can't be set yet (that's F1+F2), but the admin can prepare the schema.

## Acceptance Criteria

- [ ] `custom_field_bc` bounded context created following DDD patterns
- [ ] `CustomFieldDefinition` entity with factory method, validation rules
- [ ] Field types: text, number, date, select, multi_select, boolean
- [ ] `field_key` auto-generated from label (slug: lowercase, underscores, max 50)
- [ ] Slug collision returns validation error: "A field with a similar name already exists"
- [ ] Options required for select/multi_select, forbidden for other types
- [ ] Max 20 fields per (company_id, entity_type) enforced
- [ ] `visible_to_employees` flag (default: true)
- [ ] Soft-delete (deactivate/activate) works correctly
- [ ] Hard delete with confirmation removes definition
- [ ] Reorder updates sort_order for all affected fields
- [ ] All endpoints require Enterprise plan (402 otherwise)
- [ ] Admin UI: Settings > Custom Fields page with entity type tabs
- [ ] Admin UI: Create/edit modal with type-specific options
- [ ] Admin UI: Reorder via arrows or drag
- [ ] Admin UI: Deactivate/delete with confirmation
- [ ] Unit + integration tests pass
- [ ] `make lint` passes

## Technical Scope

### Entities (owned by this feature)
- `CustomFieldDefinition` — full entity with all fields

### Key Components
- `src/custom_field_bc/definition/domain/entities.py`
- `src/custom_field_bc/definition/domain/enums.py` (EntityType, FieldType)
- `src/custom_field_bc/definition/domain/exceptions.py`
- `src/custom_field_bc/definition/domain/repository.py`
- `src/custom_field_bc/definition/infrastructure/models.py`
- `src/custom_field_bc/definition/infrastructure/repository.py`
- `src/custom_field_bc/definition/application/commands/` (create, update, delete, deactivate, activate, reorder)
- `src/custom_field_bc/definition/application/queries/` (list, get)
- `src/custom_field_bc/definition/application/dtos.py`
- `adapters/http/api/custom_fields/routers.py`
- `adapters/http/api/custom_fields/schemas.py`
- `adapters/http/api/custom_fields/dependencies.py`
- `alembic/versions/..._create_custom_field_definitions.py`
- `web/app/src/pages/admin/CustomFieldsPage.tsx`
- Unit tests + integration tests
