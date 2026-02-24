# Implementation Tasks: F1 — Entity Integration

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 13
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Infrastructure - Migration | 1 | S |
| Infrastructure - Models (3 BCs) | 1 | S |
| Domain - Entity updates (3 BCs) | 1 | S |
| Infrastructure - Repository mappers (3 BCs) | 1 | M |
| Application - Validation Service | 1 | M |
| Application - Enrichment Service | 1 | M |
| Application - Command updates (3 BCs) | 1 | M |
| HTTP - Schema updates (3 BCs) | 1 | S |
| HTTP - Router updates (3 BCs) | 1 | L |
| MCP Server | 1 | S |
| CSV Import | 1 | M |
| Seed Data | 1 | S |
| Tests | 1 | L |

---

## Phase 1: Infrastructure

### TASK-001: Migration — Add custom_fields_data JSONB Column

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** F0 complete

**File:** `alembic/versions/k2l3m4n5o6p7_add_custom_fields_data.py`

**Implementation:**
```python
def upgrade() -> None:
    op.add_column("assets", sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("requests", sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("incidents", sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False))

def downgrade() -> None:
    op.drop_column("incidents", "custom_fields_data")
    op.drop_column("requests", "custom_fields_data")
    op.drop_column("assets", "custom_fields_data")
```

**Acceptance Criteria:**
- [x] JSONB column added to 3 tables
- [x] Default `{}` (empty JSON object)
- [x] Reversible downgrade

---

### TASK-002: Update ORM Models

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Files:**
- `src/asset_bc/asset/infrastructure/models.py`
- `src/request_bc/request/infrastructure/models.py`
- `src/incident_bc/incident/infrastructure/models.py`

**Implementation:**
Add to each model:
```python
custom_fields_data: Mapped[Any] = mapped_column(JSON, server_default="{}", nullable=False)
```

**Acceptance Criteria:**
- [x] Column added to `AssetModel`
- [x] Column added to `RequestModel` (or equivalent)
- [x] Column added to `IncidentModel` (or equivalent)

---

### TASK-003: Update Domain Entities

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Files:**
- `src/asset_bc/asset/domain/entities.py`
- `src/request_bc/request/domain/entities.py`
- `src/incident_bc/incident/domain/entities.py`

**Implementation:**
Add field to each entity `@dataclass`:
```python
custom_fields_data: dict = field(default_factory=dict)
```
Update `create()` and `update()` methods to accept `custom_fields_data` parameter.

**Acceptance Criteria:**
- [x] Field added to Asset, Request, Incident entities
- [x] `create()` accepts `custom_fields_data`
- [x] `update()` accepts `custom_fields_data`
- [x] Default is empty dict

---

### TASK-004: Update Repository Mappers

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002, TASK-003

**Files:**
- `src/asset_bc/asset/infrastructure/repository.py`
- `src/request_bc/request/infrastructure/repository.py`
- `src/incident_bc/incident/infrastructure/repository.py`

**Implementation:**
Update `_entity_to_model()` and `_model_to_entity()` in each repository to include `custom_fields_data`. Handle `None` → `{}` conversion if needed.

**Acceptance Criteria:**
- [x] Entity→Model includes `custom_fields_data`
- [x] Model→Entity includes `custom_fields_data`
- [x] Null/None handling (default to `{}`)

---

## Phase 2: Application Layer

### TASK-005: Create Validation Service

**Phase:** Application
**Complexity:** M
**Dependencies:** F0 TASK-004 (repo interface)

**File:** `src/custom_field_bc/definition/application/services/validation_service.py`

**Implementation:**
```python
class CustomFieldValidationService:
    def __init__(self, definition_repo: CustomFieldDefinitionRepositoryInterface):
        self.definition_repo = definition_repo

    def validate_for_save(self, company_id: str, entity_type: str, data: dict) -> dict:
        """Validate and clean custom_fields_data. Enforces required fields."""

    def _validate_value(self, defn: CustomFieldDefinition, value: Any) -> Any:
        """Per-type validation:
        - text: must be str
        - number: must be int/float (or convertible)
        - date: must be ISO 8601 date string
        - boolean: must be bool
        - select: must be in defn.options
        - multi_select: must be list, all items in defn.options
        """
```

Raises `ValueError` with descriptive message on validation failure.

**Acceptance Criteria:**
- [x] Validates all 6 field types
- [x] Enforces required fields (raises if missing)
- [x] Strips unknown keys (deleted fields ignored)
- [x] Returns cleaned dict with correct types
- [x] Select values validated against options
- [x] Multi-select: all values must be in options

---

### TASK-006: Create Enrichment Service

**Phase:** Application
**Complexity:** M
**Dependencies:** F0 TASK-004 (repo interface)

**File:** `src/custom_field_bc/definition/application/services/enrichment_service.py`

**Implementation:**
```python
class CustomFieldEnrichmentService:
    def __init__(self, definition_repo: CustomFieldDefinitionRepositoryInterface):
        self.definition_repo = definition_repo

    def enrich(self, company_id: str, entity_type: str, custom_fields_data: dict) -> list[dict]:
        """Pair values with definitions. Returns enriched array sorted by sort_order."""

    def enrich_batch(self, company_id: str, entity_type: str, entities_data: list[dict]) -> list[list[dict]]:
        """Enrich multiple entities with one definition query."""
```

Each enriched item: `{key, label, type, value, required, is_active, visible_to_employees, options?}`

**Acceptance Criteria:**
- [x] Returns enriched array sorted by `sort_order`
- [x] Includes inactive field definitions (marked `is_active: false`)
- [x] Missing values shown as `null`
- [x] Options included only for select/multi_select
- [x] `enrich_batch` makes only 1 definition query for N entities

---

### TASK-007: Update Create/Update Commands

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003

**Files:**
- `src/asset_bc/asset/application/commands/create_asset.py`
- Asset update command (if separate file)
- Request create/update commands
- Incident create/update commands

**Implementation:**
Add `custom_fields_data: dict = field(default_factory=dict)` to each command dataclass. Pass through to entity `create()`/`update()` methods.

**Acceptance Criteria:**
- [x] All create commands accept `custom_fields_data`
- [x] All update commands accept `custom_fields_data`
- [x] Values passed through to entity methods

---

## Phase 3: HTTP Layer

### TASK-008: Update Schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-005, TASK-006

**Files:**
- `adapters/http/api/assets/schemas.py`
- Request schemas file
- Incident schemas file

**Implementation:**
Add to create/update request schemas:
```python
custom_fields_data: Optional[dict[str, Any]] = None
```
Add to response schemas:
```python
custom_fields: Optional[list[dict[str, Any]]] = None
```

**Acceptance Criteria:**
- [x] Request schemas accept `custom_fields_data`
- [x] Response schemas include `custom_fields`
- [x] Both are Optional (backward compatible)

---

### TASK-009: Update Routers (Validate + Enrich)

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-005, TASK-006, TASK-007, TASK-008

**Files:**
- `adapters/http/api/assets/routers.py`
- Request router
- Incident router
- `adapters/http/api/custom_fields/dependencies.py` — add `get_cf_validation_service`, `get_cf_enrichment_service`

**Implementation per router:**
- Inject `CustomFieldValidationService` and `CustomFieldEnrichmentService` via Depends
- **On create/update**: call `validator.validate_for_save(company_id, entity_type, body.custom_fields_data)` before dispatching command. Catch `ValueError` → `HTTPException(422)`.
- **On GET single**: call `enricher.enrich(company_id, entity_type, entity.custom_fields_data)` and add to response
- **On GET list**: call `enricher.enrich_batch(...)` and add to each response item

**Acceptance Criteria:**
- [x] Asset create validates custom fields before saving
- [x] Asset update validates custom fields before saving
- [x] Asset GET single returns enriched `custom_fields`
- [x] Asset GET list returns enriched `custom_fields` per item
- [x] Same for request and incident routers
- [x] Validation errors return 422

---

### TASK-010: Update MCP Server

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-006

**File:** `adapters/mcp/server.py`

**Implementation:**
Where MCP tools return asset/request data, load enrichment service and include `custom_fields` in the text response.

**Acceptance Criteria:**
- [x] MCP asset tools include custom fields in response
- [x] MCP request tools include custom fields in response

---

### TASK-011: Update CSV Import

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Files:** CSV import service (locate existing import logic)

**Implementation:**
1. Load active definitions for entity type
2. Build `field_key → definition` map
3. For each CSV row, extract columns matching field_keys
4. Build `custom_fields_data` dict from matched columns
5. Validate with `CustomFieldValidationService`
6. Include in create command

**Acceptance Criteria:**
- [x] CSV columns matching field_keys are recognized
- [x] Values converted to correct types
- [x] Unknown columns ignored (not custom fields)
- [x] Validation errors reported per row

---

### TASK-012: Add Seed Data

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-009

**File:** `scripts/seed_demo_data.py`

**Implementation:**
Add section after companies are seeded:
- Create 5 custom field definitions for assets (Cost Center, Insurance Policy, Building, Is Leased, Floor)
- Create 2 for requests (Budget Code, Urgency Reason)
- Create 2 for incidents (Affected Systems, External Vendor)
- Assign sample values to existing demo assets/requests/incidents

**Acceptance Criteria:**
- [x] 9 sample definitions created across 3 entity types
- [x] Sample values assigned to demo entities
- [x] `make seed` works without errors

---

## Phase 4: Tests

### TASK-013: Unit + Integration Tests

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-009

**Files:**
- `tests/unit/custom_field_bc/definition/application/services/test_validation_service.py`
- `tests/unit/custom_field_bc/definition/application/services/test_enrichment_service.py`
- `tests/integration/test_custom_fields_integration.py` (or extend `test_custom_fields_endpoints.py`)

**Unit tests — ValidationService:**
- Text field: valid string, rejects non-string
- Number field: valid int/float, rejects string
- Date field: valid ISO date, rejects bad format
- Boolean field: valid bool, rejects string
- Select field: valid option, rejects invalid option
- Multi-select: valid array of options, rejects invalid items
- Required field missing → error
- Unknown key stripped
- Empty dict → valid (no required fields)

**Unit tests — EnrichmentService:**
- Returns all definitions sorted by sort_order
- Includes inactive definitions
- Missing values → null
- Options included for select types
- Batch enrichment: 1 query for N entities

**Integration tests:**
- POST create asset with custom_fields_data → 201, values persisted
- GET asset → custom_fields enriched in response
- PUT update asset custom fields → values updated
- POST create asset with invalid custom field → 422
- POST create asset with missing required custom field → 422
- GET asset list → each item has custom_fields

**Acceptance Criteria:**
- [x] ValidationService: all 6 types tested + required + unknown keys
- [x] EnrichmentService: sorting, batch, inactive
- [x] Integration: create/read/update with custom fields
- [x] Integration: validation errors
- [x] `make test` passes
- [x] `make test-integration` passes

---

## Dependency Graph

```
F0 complete
    │
    ├── TASK-001 (Migration) → TASK-002 (Models) → TASK-004 (Repo Mappers)
    ├── TASK-003 (Entities) ────────────────────────┘       │
    │                                                        │
    ├── TASK-005 (Validation Svc) ◄─────────────────────────┘
    ├── TASK-006 (Enrichment Svc) ◄─────────────────────────┘
    │       │           │
    │       ├── TASK-007 (Command Updates)
    │       ├── TASK-008 (Schema Updates)
    │       │           │
    │       └── TASK-009 (Router Updates) ◄── TASK-007 + TASK-008
    │               │
    │       TASK-010 (MCP) ◄── TASK-006
    │       TASK-011 (CSV) ◄── TASK-005
    │       TASK-012 (Seed) ◄── TASK-009
    │
    └── TASK-013 (Tests) ◄── TASK-009
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-003
**Batch 2:** TASK-002
**Batch 3 (Parallel):** TASK-004, TASK-005, TASK-006
**Batch 4 (Parallel):** TASK-007, TASK-008
**Batch 5:** TASK-009
**Batch 6 (Parallel):** TASK-010, TASK-011, TASK-012
**Batch 7:** TASK-013

## Final Checklist

- [x] All 13 tasks completed
- [x] `make test` passes
- [x] `make test-integration` passes
- [x] `make lint` passes
- [x] `make seed` works
- [x] MCP tools return custom fields
