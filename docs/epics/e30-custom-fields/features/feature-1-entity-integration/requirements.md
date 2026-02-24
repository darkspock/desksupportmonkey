# Feature 1: Entity Integration

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0
**Complexity:** L

## Scope

### Included
- Alembic migration: add `custom_fields_data JSONB DEFAULT '{}'` column to `assets`, `requests`, `incidents` tables
- Update SQLAlchemy models for Asset, Request, Incident to include `custom_fields_data`
- Update domain entities to carry `custom_fields_data: dict`
- Update existing create/update commands to accept and persist `custom_fields_data`
- Custom field validation service: validates values against active definitions (type checking, required fields, option validation)
- Required field behavior: validate only on save, not retroactively on existing entities
- Select option removal: preserved values displayed normally, removed options can't be re-selected
- Response enrichment: entity GET endpoints return enriched `custom_fields: [...]` array (paired with definitions for labels/types/options)
- MCP server: include `custom_fields` in asset/request responses
- CSV import: recognize custom field columns by `field_key`
- Audit trail: custom field value changes captured with old/new values
- Seed data: 3-5 example custom fields per entity type with sample values in demo script
- Update `tests/conftest.py` with model changes
- Unit tests: validation service (type checking, required fields, option validation)
- Integration tests: entity create/update with custom fields, enrichment on GET

### Excluded (in other features)
- Frontend form rendering (F2)
- Frontend detail page display (F2)
- Search/filter by custom field values (F3)
- PDF/CSV export of custom fields (F3)

## User Value

After this feature, the API fully supports custom fields. Creating/editing assets, requests, and incidents via API includes custom field data. Responses are enriched with field metadata. MCP tools return custom fields. CSV import handles custom field columns. The backend is complete — only frontend rendering remains.

## Acceptance Criteria

- [ ] `custom_fields_data` JSONB column added to assets, requests, incidents tables
- [ ] Asset/request/incident create endpoints accept `custom_fields_data` in body
- [ ] Asset/request/incident update endpoints accept `custom_fields_data` in body
- [ ] Validation service checks: required fields present, number values numeric, select values from options, multi_select values all from options, date values ISO format, boolean values true/false
- [ ] Required field validation only on save (existing entities without values are not blocked)
- [ ] Enriched `custom_fields` array in GET responses includes: key, label, type, value, required, options (for select types), visible_to_employees
- [ ] Inactive field values included in enrichment (marked as inactive)
- [ ] Deleted field keys in JSONB are ignored (no error on read)
- [ ] MCP asset/request tools include `custom_fields` in responses
- [ ] CSV import recognizes custom field columns by `field_key` and stores values
- [ ] Audit middleware captures custom field value changes
- [ ] Seed data script includes sample custom fields for demo companies
- [ ] Unit + integration tests pass
- [ ] `make lint` passes

## Technical Scope

### Entities (modified by this feature)
- `Asset` entity — add `custom_fields_data: dict` field
- `Request` entity — add `custom_fields_data: dict` field
- `Incident` entity — add `custom_fields_data: dict` field

### Entities (used from F0)
- `CustomFieldDefinition` — read definitions for validation and enrichment

### Key Components
- `alembic/versions/..._add_custom_fields_data.py` — migration
- `src/asset_bc/asset/domain/entities.py` — add field
- `src/asset_bc/asset/infrastructure/models.py` — add column
- `src/request_bc/request/domain/entities.py` — add field
- `src/request_bc/request/infrastructure/models.py` — add column
- `src/incident_bc/incident/domain/entities.py` — add field
- `src/incident_bc/incident/infrastructure/models.py` — add column
- `src/custom_field_bc/definition/application/services/validation_service.py` — validates values against definitions
- `src/custom_field_bc/definition/application/services/enrichment_service.py` — enriches entity responses
- `adapters/http/api/assets/routers.py` — inject enrichment
- `adapters/http/api/assets/schemas.py` — add custom_fields to response
- Same for requests and incidents routers/schemas
- `adapters/mcp/server.py` — include custom_fields
- `scripts/seed_demo_data.py` — add sample custom fields
- CSV import service modifications

## Notes

- The validation service is injected in entity routers via FastAPI dependencies (same pattern as other cross-BC services).
- Enrichment is done at the HTTP layer, not in the domain. The domain entity carries raw `custom_fields_data` dict; the router enriches it with definition metadata for the response.
