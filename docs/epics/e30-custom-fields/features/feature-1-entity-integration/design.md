# Solution Design: F1 — Entity Integration

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-24
**Bounded Contexts:** `asset_bc`, `request_bc`, `incident_bc`, `custom_field_bc`

## Summary

Add `custom_fields_data JSONB` column to assets, requests, and incidents tables. Modify create/update commands and endpoints to accept and persist custom field data. Build validation and enrichment services in `custom_field_bc`. Integrate with MCP, CSV import, audit trail, and seed data.

## Architecture Decision

Values stored as JSONB on each entity (not EAV). The `custom_field_bc` provides two cross-BC services:
- **ValidationService** — validates `custom_fields_data` dict against active definitions
- **EnrichmentService** — pairs raw values with definition metadata for API responses

These services are injected in target BC routers via FastAPI `Depends()`, following the same cross-BC pattern as shipping_bc injecting AssetRepository.

## Existing Code Analysis

| Component | Location | Modifications Needed |
|-----------|----------|---------------------|
| Asset entity | `src/asset_bc/asset/domain/entities.py` | Add `custom_fields_data: dict` field |
| Asset model | `src/asset_bc/asset/infrastructure/models.py` | Add `custom_fields_data` JSONB column |
| Asset create command | `src/asset_bc/asset/application/commands/create_asset.py` | Accept `custom_fields_data` |
| Asset router | `adapters/http/api/assets/routers.py` | Validate + enrich custom fields |
| Asset schemas | `adapters/http/api/assets/schemas.py` | Add `custom_fields_data` to request, `custom_fields` to response |
| Request entity/model/commands/router/schemas | Same pattern as assets | Same changes |
| Incident entity/model/commands/router/schemas | Same pattern as assets | Same changes |
| MCP server | `adapters/mcp/server.py` | Include custom_fields in responses |
| Seed script | `scripts/seed_demo_data.py` | Add sample custom fields |

## Implementation Plan

### 1. Domain Layer Changes

#### Asset Entity (modify)
```python
# Add to Asset dataclass
custom_fields_data: dict = field(default_factory=dict)

# Update create() to accept custom_fields_data
# Update update() to accept custom_fields_data
```

Same pattern for Request and Incident entities.

#### Validation Service (new)
**File:** `src/custom_field_bc/definition/application/services/validation_service.py`

```python
class CustomFieldValidationService:
    def __init__(self, definition_repo: CustomFieldDefinitionRepositoryInterface):
        self.definition_repo = definition_repo

    def validate(self, company_id: str, entity_type: str, data: dict) -> dict:
        """Validate custom_fields_data against active definitions.
        Returns cleaned data dict (only known keys, correct types).
        Raises ValidationError if required fields missing or type mismatch."""
        definitions = self.definition_repo.find_active_by_entity_type(company_id, entity_type)
        active_keys = {d.field_key: d for d in definitions}
        cleaned = {}

        for key, value in data.items():
            if key not in active_keys:
                continue  # ignore unknown keys (deleted fields)
            defn = active_keys[key]
            cleaned[key] = self._validate_value(defn, value)

        # Check required fields
        for defn in definitions:
            if defn.required and defn.field_key not in cleaned:
                # Only enforce on explicit saves, not retroactively
                pass  # Caller decides whether to enforce

        return cleaned

    def validate_for_save(self, company_id: str, entity_type: str, data: dict) -> dict:
        """Same as validate but enforces required fields."""
        # ... raises if required field missing

    def _validate_value(self, defn, value):
        """Type-check and coerce: number→float, boolean→bool, select→in options, etc."""
```

#### Enrichment Service (new)
**File:** `src/custom_field_bc/definition/application/services/enrichment_service.py`

```python
class CustomFieldEnrichmentService:
    def __init__(self, definition_repo: CustomFieldDefinitionRepositoryInterface):
        self.definition_repo = definition_repo

    def enrich(self, company_id: str, entity_type: str, custom_fields_data: dict) -> list[dict]:
        """Pair raw values with definitions for API response."""
        definitions = self.definition_repo.find_by_entity_type(company_id, entity_type)
        result = []
        for defn in sorted(definitions, key=lambda d: d.sort_order):
            entry = {
                "key": defn.field_key,
                "label": defn.label,
                "type": defn.field_type,
                "value": custom_fields_data.get(defn.field_key),
                "required": defn.required,
                "is_active": defn.is_active,
                "visible_to_employees": defn.visible_to_employees,
            }
            if defn.field_type in ("select", "multi_select"):
                entry["options"] = defn.options
            result.append(entry)
        return result

    def enrich_batch(self, company_id: str, entity_type: str, entities: list) -> dict[str, list[dict]]:
        """Enrich multiple entities at once (1 definition query, N enrichments)."""
        definitions = self.definition_repo.find_by_entity_type(company_id, entity_type)
        # ... same logic but definitions fetched once
```

### 2. Infrastructure Layer Changes

#### Migration
**File:** `alembic/versions/..._add_custom_fields_data.py`

```python
def upgrade() -> None:
    op.add_column("assets", sa.Column("custom_fields_data", sa.JSON(), server_default="{}"))
    op.add_column("requests", sa.Column("custom_fields_data", sa.JSON(), server_default="{}"))
    op.add_column("incidents", sa.Column("custom_fields_data", sa.JSON(), server_default="{}"))

def downgrade() -> None:
    op.drop_column("incidents", "custom_fields_data")
    op.drop_column("requests", "custom_fields_data")
    op.drop_column("assets", "custom_fields_data")
```

#### Model Changes
Add to `AssetModel`, `RequestModel`, `IncidentModel`:
```python
custom_fields_data: Mapped[Any] = mapped_column(JSON, server_default="{}", nullable=False)
```

#### Repository Changes
Update `_entity_to_model()` and `_model_to_entity()` in each repository to include `custom_fields_data`.

### 3. Application Layer Changes

#### Command Changes (modify existing)
Update these existing commands to accept and pass through `custom_fields_data`:
- `CreateAssetCommand` / handler
- `UpdateAssetCommand` / handler (if exists, or the update flow)
- Same for Request and Incident create/update commands

The command just carries the dict; validation happens at the HTTP layer before dispatching.

### 4. HTTP Layer Changes

#### Schema Changes
Add to request schemas:
```python
class CreateAssetRequest(BaseModel):
    # ... existing fields ...
    custom_fields_data: Optional[dict[str, Any]] = None
```

Add to response schemas:
```python
class AssetResponse(BaseModel):
    # ... existing fields ...
    custom_fields: Optional[list[dict[str, Any]]] = None
```

#### Router Changes
In asset router (and request/incident routers):
```python
# Inject validation and enrichment services
def get_cf_validation_service(db=Depends(get_db)):
    return CustomFieldValidationService(CustomFieldDefinitionRepository(db))

def get_cf_enrichment_service(db=Depends(get_db)):
    return CustomFieldEnrichmentService(CustomFieldDefinitionRepository(db))

# On create/update: validate before dispatching command
@router.post("/")
async def create_asset(
    body: CreateAssetRequest,
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    ...
):
    cf_data = {}
    if body.custom_fields_data:
        cf_data = cf_validator.validate_for_save(company_id, "asset", body.custom_fields_data)
    # ... create command with custom_fields_data=cf_data

# On GET: enrich response
@router.get("/{id}")
async def get_asset(
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
    ...
):
    # ... load asset
    custom_fields = cf_enricher.enrich(company_id, "asset", asset.custom_fields_data or {})
    return {"data": {**_to_response(asset), "custom_fields": custom_fields}}

# On list: enrich batch
@router.get("/")
async def list_assets(
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
    ...
):
    # ... load assets
    cf_map = cf_enricher.enrich_batch(company_id, "asset", assets)
    # ... attach to each response
```

### 5. MCP Server Changes

In `adapters/mcp/server.py`, modify asset/request tools to include `custom_fields` in text responses. Load enrichment service in the tool handler.

### 6. CSV Import Changes

Modify the CSV import service to:
1. Load active field definitions for entity type
2. Map CSV column headers to `field_key` values
3. Populate `custom_fields_data` dict from CSV row
4. Include in create command

### 7. Audit Trail

Custom field changes are automatically captured by the audit middleware since it logs request bodies on write operations. The JSONB diff between old and new `custom_fields_data` provides the change trail.

### 8. Seed Data

In `scripts/seed_demo_data.py`, add after companies/assets are seeded:
```python
# Sample custom field definitions
sample_definitions = [
    {"entity_type": "asset", "label": "Cost Center", "field_type": "text", "required": True},
    {"entity_type": "asset", "label": "Insurance Policy", "field_type": "text", "required": False},
    {"entity_type": "asset", "label": "Building", "field_type": "select", "options": ["HQ", "Branch A", "Branch B", "Remote"]},
    {"entity_type": "asset", "label": "Is Leased", "field_type": "boolean"},
    {"entity_type": "asset", "label": "Floor", "field_type": "number"},
    {"entity_type": "request", "label": "Budget Code", "field_type": "text"},
    {"entity_type": "request", "label": "Urgency Reason", "field_type": "select", "options": ["Business Critical", "Standard", "Low Priority"]},
    {"entity_type": "incident", "label": "Affected Systems", "field_type": "multi_select", "options": ["Email", "VPN", "CRM", "ERP", "Network"]},
    {"entity_type": "incident", "label": "External Vendor", "field_type": "text"},
]
# Then assign sample values to demo assets/requests/incidents
```

### 5. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/entities.py` | Add field | `custom_fields_data: dict` |
| `src/asset_bc/asset/infrastructure/models.py` | Add column | JSONB column |
| `src/asset_bc/asset/infrastructure/repository.py` | Update mappers | Include `custom_fields_data` |
| `src/asset_bc/asset/application/commands/create_asset.py` | Add param | `custom_fields_data` |
| `adapters/http/api/assets/routers.py` | Inject services | Validation + enrichment |
| `adapters/http/api/assets/schemas.py` | Add fields | Request + response |
| Same 6 files for `request_bc` | Same changes | — |
| Same 6 files for `incident_bc` | Same changes | — |
| `adapters/mcp/server.py` | Enrich responses | Add custom_fields |
| `scripts/seed_demo_data.py` | Add section | Sample definitions + values |
| CSV import service | Extend logic | Map columns to field_keys |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | ValidationService — all 6 field types, required enforcement, unknown key filtering | High |
| Unit | EnrichmentService — pairing, batch, inactive fields included | High |
| Unit | Modified create/update command handlers | High |
| Integration | Asset create with custom_fields_data | High |
| Integration | Asset GET with enriched custom_fields | High |
| Integration | Asset update custom_fields_data | High |
| Integration | Request/incident same flows | High |
| Integration | Invalid type value rejected (422) | Medium |
| Integration | Required field missing rejected | Medium |
| Integration | Deleted field key ignored on read | Medium |

## Implementation Order

1. [ ] Migration: add `custom_fields_data` JSONB to 3 tables
2. [ ] Update models (Asset, Request, Incident)
3. [ ] Update domain entities
4. [ ] Update repository mappers
5. [ ] Build ValidationService
6. [ ] Build EnrichmentService
7. [ ] Update create/update commands
8. [ ] Update HTTP dependencies (CF service factories)
9. [ ] Update asset router + schemas (validate on write, enrich on read)
10. [ ] Update request router + schemas
11. [ ] Update incident router + schemas
12. [ ] Update MCP server
13. [ ] Update CSV import
14. [ ] Add seed data
15. [ ] Unit tests
16. [ ] Integration tests
17. [ ] `make lint`
