# Implementation Tasks: F1 — CI Relationships

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-26
**Total Tasks:** 20
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Enums | 1 | S |
| Domain — Entities | 1 | M |
| Domain — Interfaces | 1 | S |
| Infrastructure — Migration | 1 | S |
| Infrastructure — Models | 1 | S |
| Infrastructure — Repositories | 1 | M |
| Application — Commands | 3 | M |
| Application — Queries | 1 | S |
| HTTP — Schemas | 1 | S |
| HTTP — Dependencies | 1 | S |
| HTTP — Router | 1 | M |
| HTTP — Mount | 1 | S |
| Tests — Unit (Domain) | 1 | S |
| Tests — Unit (Commands) | 3 | M |
| Tests — Unit (Queries) | 1 | S |
| Tests — Integration | 1 | M |
| Frontend — Types + Dependencies Tab + i18n | 1 | L |
| Verification | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create CIRelationshipType Enum

**Phase:** Domain — Enums
**Complexity:** S
**Dependencies:** None

**Description:**
Add `CIRelationshipType` enum to the existing enums file.

**File:** `src/asset_bc/asset/domain/enums.py` (modify)

**Implementation:**
```python
class CIRelationshipType(str, Enum):
    RUNS_ON = "runs_on"
    DEPENDS_ON = "depends_on"
    CONNECTED_TO = "connected_to"
    PART_OF = "part_of"
    BACKS_UP = "backs_up"
```

**Acceptance Criteria:**
- [x] 5 values: runs_on, depends_on, connected_to, part_of, backs_up
- [x] Inherits from `str, Enum` for JSON serialization

---

### TASK-002: Create CIRelationship Entity

**Phase:** Domain — Entities
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Add `CIRelationship` dataclass to the existing entities file. Factory `create()` method with ULID generation. `update_description()` method returns change dict for audit trail.

**File:** `src/asset_bc/asset/domain/entities.py` (modify)

**Implementation:**
```python
@dataclass
class CIRelationship:
    id: str
    company_id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: CIRelationshipType
    description: Optional[str]
    created_at: datetime
    created_by: str

    @classmethod
    def create(cls, company_id, source_asset_id, target_asset_id,
               relationship_type, created_by, description=None) -> "CIRelationship":
        return cls(
            id=generate_ulid(),
            company_id=company_id,
            source_asset_id=source_asset_id,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            description=description,
            created_at=datetime.utcnow(),
            created_by=created_by,
        )

    def update_description(self, description: Optional[str]) -> dict:
        old = self.description
        self.description = description
        if old != description:
            return {"description": {"old": old, "new": description}}
        return {}
```

**Acceptance Criteria:**
- [x] Dataclass with all 8 fields from design
- [x] `create()` classmethod generates ULID and sets created_at
- [x] `update_description()` returns change dict when value changes
- [x] `update_description()` returns empty dict when no change
- [x] Import CIRelationshipType from enums

---

### TASK-003: Create CIRelationshipRepositoryInterface

**Phase:** Domain — Interfaces
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `CIRelationshipRepositoryInterface` abstract class to the existing repository interface file.

**File:** `src/asset_bc/asset/domain/repository.py` (modify)

**Methods (exactly as in design):**
- `save(relationship: CIRelationship) -> CIRelationship` — upsert
- `find_by_id(relationship_id: str, company_id: str) -> Optional[CIRelationship]`
- `find_by_asset(asset_id: str, company_id: str) -> list[CIRelationship]` — both directions
- `find_duplicate(source_asset_id: str, target_asset_id: str, relationship_type: str, company_id: str) -> Optional[CIRelationship]`
- `delete(relationship_id: str) -> None` — hard delete

**Acceptance Criteria:**
- [x] ABC abstract class
- [x] All 5 methods with correct signatures from design
- [x] Import CIRelationship entity
- [x] All methods decorated with `@abstractmethod`

---

## Phase 2: Infrastructure Layer

### TASK-004: Create CIRelationshipModel

**Phase:** Infrastructure — Models
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Add `CIRelationshipModel` to the existing models file.

**File:** `src/asset_bc/asset/infrastructure/models.py` (modify)

**Implementation:**
```python
class CIRelationshipModel(Base, ULIDMixin, TimestampMixin):
    __tablename__ = "ci_relationships"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    source_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    target_asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(String(26))

    __table_args__ = (
        UniqueConstraint("source_asset_id", "target_asset_id", "relationship_type",
                         name="uq_ci_rel_source_target_type"),
    )
```

**Acceptance Criteria:**
- [x] Uses `Mapped[type]` annotations (SQLAlchemy 2.0)
- [x] Uses `ULIDMixin` and `TimestampMixin`
- [x] ForeignKey to `companies.id`, `assets.id` (source + target)
- [x] Indexes on company_id, source_asset_id, target_asset_id
- [x] UniqueConstraint on (source_asset_id, target_asset_id, relationship_type)
- [x] description is nullable, max 500 chars

---

### TASK-005: Create ci_relationships Migration

**Phase:** Infrastructure — Migration
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create Alembic migration for the `ci_relationships` table.

**File:** `alembic/versions/xxx_create_ci_relationships_table.py` (new)

**Schema:**
```sql
CREATE TABLE ci_relationships (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    source_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    target_asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    relationship_type VARCHAR(20) NOT NULL,
    description VARCHAR(500),
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ci_rel_source_target_type UNIQUE (source_asset_id, target_asset_id, relationship_type)
);

CREATE INDEX ix_ci_relationships_company_id ON ci_relationships(company_id);
CREATE INDEX ix_ci_relationships_source ON ci_relationships(source_asset_id);
CREATE INDEX ix_ci_relationships_target ON ci_relationships(target_asset_id);
```

**Acceptance Criteria:**
- [x] All columns from design
- [x] Foreign keys to companies and assets tables
- [x] 3 indexes (company_id, source, target)
- [x] Unique constraint on (source, target, type)
- [x] Reversible (downgrade drops table)

---

### TASK-006: Create CIRelationshipRepository

**Phase:** Infrastructure — Repositories
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Create the CIRelationship repository implementation in a separate file.

**File:** `src/asset_bc/asset/infrastructure/ci_relationship_repository.py` (new)

**Methods:**
- `save()` — upsert pattern: check existing by ID, update fields or create new model, flush+refresh, return entity
- `find_by_id()` — single lookup with company_id filter
- `find_by_asset()` — `WHERE source_asset_id = X OR target_asset_id = X AND company_id = Y`
- `find_duplicate()` — `WHERE source + target + type + company_id match`
- `delete()` — load by ID, `session.delete()` for hard delete

**Static conversion methods:**
- `_to_entity(model) -> CIRelationship` — model to domain entity, converts relationship_type string to enum
- `_to_model(entity) -> CIRelationshipModel` — entity to model for creation

**Acceptance Criteria:**
- [x] Implements `CIRelationshipRepositoryInterface`
- [x] Constructor takes `Session`
- [x] `_to_entity()` converts string to CIRelationshipType enum
- [x] `save()` uses upsert pattern (following AssetRepository)
- [x] `find_by_asset()` returns relationships in BOTH directions (source OR target)
- [x] `delete()` performs hard delete
- [x] All queries filter by company_id

---

## Phase 3: Application Layer

### TASK-007: Create CreateCIRelationshipCommand + Handler

**Phase:** Application — Commands
**Complexity:** M
**Dependencies:** TASK-002, TASK-003, TASK-006

**Description:**
Command and handler for creating CI relationships with full constraint validation.

**File:** `src/asset_bc/asset/application/commands/create_ci_relationship.py` (new)

**Command fields:**
- `company_id: str`
- `source_asset_id: str`
- `target_asset_id: str`
- `relationship_type: str`
- `description: Optional[str]`
- `performed_by: str`

**Handler logic (in order):**
1. Validate source != target → `SelfReferenceError`
2. Load source asset via `asset_repo.find_by_id(source_asset_id, company_id)` → `AssetNotFoundError` if None
3. Load target asset via `asset_repo.find_by_id(target_asset_id, company_id)` → `AssetNotFoundError` if None (validates same company)
4. Check target not decommissioned → `DecommissionedTargetError`
5. Check no duplicate via `ci_repo.find_duplicate(...)` → `DuplicateRelationshipError`
6. Create `CIRelationship.create(...)` entity
7. Save via `ci_repo.save(relationship)`
8. Record `AssetEvent` on source: event_type=`ci_relationship_created`, data=`{relationship_id, target_asset_id, relationship_type}`
9. Return None

**Handler constructor dependencies:**
- `asset_repo: AssetRepositoryInterface`
- `ci_repo: CIRelationshipRepositoryInterface`

**Domain exceptions (defined in this file, following existing pattern):**
- `SelfReferenceError`
- `DuplicateRelationshipError`
- `DecommissionedTargetError`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler` base classes
- [x] All 5 constraint validations in correct order
- [x] Creates CIRelationship entity via factory
- [x] Records AssetEvent with correct event_type and data
- [x] Returns None (CQRS)
- [x] Domain exceptions defined with descriptive messages

---

### TASK-008: Create UpdateCIRelationshipCommand + Handler

**Phase:** Application — Commands
**Complexity:** S
**Dependencies:** TASK-002, TASK-003, TASK-006

**Description:**
Command and handler for updating CI relationship description.

**File:** `src/asset_bc/asset/application/commands/update_ci_relationship.py` (new)

**Command fields:**
- `relationship_id: str`
- `company_id: str`
- `description: Optional[str]`
- `performed_by: str`

**Handler logic:**
1. Load relationship via `ci_repo.find_by_id(relationship_id, company_id)` → `CIRelationshipNotFoundError` if None
2. Call `relationship.update_description(command.description)`
3. If changes occurred, save via `ci_repo.save(relationship)`
4. Return None

**Handler constructor dependencies:**
- `ci_repo: CIRelationshipRepositoryInterface`

**Domain exception (defined in this file):**
- `CIRelationshipNotFoundError`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler` base classes
- [x] Loads relationship with company_id check
- [x] Only saves if actual changes occurred
- [x] Returns None (CQRS)

---

### TASK-009: Create DeleteCIRelationshipCommand + Handler

**Phase:** Application — Commands
**Complexity:** S
**Dependencies:** TASK-002, TASK-003, TASK-006

**Description:**
Command and handler for deleting CI relationships (hard delete) with audit event.

**File:** `src/asset_bc/asset/application/commands/delete_ci_relationship.py` (new)

**Command fields:**
- `relationship_id: str`
- `company_id: str`
- `source_asset_id: str`
- `performed_by: str`

**Handler logic:**
1. Load relationship via `ci_repo.find_by_id(relationship_id, company_id)` → `CIRelationshipNotFoundError` if None
2. Capture target_asset_id and relationship_type before delete
3. Delete via `ci_repo.delete(relationship.id)`
4. Record `AssetEvent` on source: event_type=`ci_relationship_deleted`, data=`{relationship_id, target_asset_id, relationship_type}`
5. Return None

**Handler constructor dependencies:**
- `asset_repo: AssetRepositoryInterface` (for save_event)
- `ci_repo: CIRelationshipRepositoryInterface`

**Acceptance Criteria:**
- [x] Inherits from `Command` / `CommandHandler` base classes
- [x] Hard deletes (not soft delete)
- [x] Records AssetEvent AFTER successful delete
- [x] Event data includes relationship_id, target_asset_id, relationship_type
- [x] Returns None (CQRS)

---

### TASK-010: Create ListCIRelationshipsQuery + Handler

**Phase:** Application — Queries
**Complexity:** S
**Dependencies:** TASK-003, TASK-006

**Description:**
Query and handler to list all CI relationships for a given asset (both directions).

**File:** `src/asset_bc/asset/application/queries/list_ci_relationships.py` (new)

**Query fields:**
- `asset_id: str`
- `company_id: str`

**Handler logic:**
1. Return `ci_repo.find_by_asset(asset_id, company_id)`

**Return type:** `list[CIRelationship]`

**Handler constructor dependencies:**
- `ci_repo: CIRelationshipRepositoryInterface`

**Acceptance Criteria:**
- [x] Inherits from `Query` / `QueryHandler` base classes
- [x] Returns `list[CIRelationship]` (domain entities)
- [x] Delegates to repository (no business logic)

---

## Phase 4: HTTP Layer

### TASK-011: Create Relationship Schemas

**Phase:** HTTP — Schemas
**Complexity:** S
**Dependencies:** None (can be written in parallel)

**Description:**
Add request/response Pydantic schemas for CI relationships to the existing schemas file.

**File:** `adapters/http/api/assets/schemas.py` (modify)

**Schemas:**

```python
class CreateCIRelationshipRequest(BaseModel):
    target_asset_id: str = Field(..., min_length=1, max_length=26)
    relationship_type: str = Field(...)
    description: Optional[str] = Field(None, max_length=500)

class UpdateCIRelationshipRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=500)

class CIRelationshipResponse(BaseModel):
    id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    description: Optional[str]
    created_at: str
    created_by: str
    target_asset_name: Optional[str] = None
    target_asset_serial: Optional[str] = None
    target_asset_type: Optional[str] = None
    target_asset_criticality: Optional[str] = None
    target_asset_status: Optional[str] = None
    source_asset_name: Optional[str] = None
    source_asset_serial: Optional[str] = None
    source_asset_type: Optional[str] = None
    source_asset_criticality: Optional[str] = None
    source_asset_status: Optional[str] = None
```

**Acceptance Criteria:**
- [x] CreateCIRelationshipRequest with target_asset_id, relationship_type, description
- [x] UpdateCIRelationshipRequest with description only
- [x] CIRelationshipResponse with all base fields + enriched asset display fields
- [x] Field validation constraints (min_length, max_length)

---

### TASK-012: Add CI Relationship Repository Dependency

**Phase:** HTTP — Dependencies
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
Add dependency injection function for `CIRelationshipRepository`.

**File:** `adapters/http/api/assets/dependencies.py` (modify)

**Implementation:**
```python
def get_ci_relationship_repo(db: Session = Depends(get_db)) -> CIRelationshipRepository:
    return CIRelationshipRepository(db)
```

**Acceptance Criteria:**
- [x] Function creates CIRelationshipRepository with DB session
- [x] Follows existing pattern from `get_asset_repo()`

---

### TASK-013: Create Relationship Router

**Phase:** HTTP — Router
**Complexity:** M
**Dependencies:** TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012

**Description:**
Create sub-router for CI relationship endpoints.

**File:** `adapters/http/api/assets/relationship_router.py` (new)

**Endpoints:**
1. `POST /` — Create relationship (201)
   - Gets asset_id from path, user from auth
   - Executes CreateCIRelationshipCommand
   - Returns enriched CIRelationshipResponse
2. `GET /` — List relationships
   - Gets asset_id from path
   - Executes ListCIRelationshipsQuery
   - Batch-resolves asset display data (names, serials, criticality)
   - Returns list of enriched CIRelationshipResponse
3. `PATCH /{relationship_id}` — Update description
   - Executes UpdateCIRelationshipCommand
   - Returns enriched CIRelationshipResponse
4. `DELETE /{relationship_id}` — Delete relationship (204)
   - Executes DeleteCIRelationshipCommand
   - Returns 204 No Content

**Error mapping:**
- AssetNotFoundError → 404
- CIRelationshipNotFoundError → 404
- SelfReferenceError → 422
- DuplicateRelationshipError → 409
- DecommissionedTargetError → 422

**Response enrichment (batch):**
- Collect all unique source/target asset IDs from relationships
- Load all assets in one query via `asset_repo.find_all_by_company()` or individual lookups
- Build display name (`{brand} {model}`), serial, type, criticality, status for each
- Attach to response

**Acceptance Criteria:**
- [x] 4 endpoints: POST, GET, PATCH, DELETE
- [x] All domain exceptions caught and mapped to correct HTTP status codes
- [x] POST returns 201, DELETE returns 204
- [x] Response enrichment with target/source asset display data
- [x] Auth: admin or technician roles
- [x] asset_id from path parameter

---

### TASK-014: Mount Relationship Router

**Phase:** HTTP — Mount
**Complexity:** S
**Dependencies:** TASK-013

**Description:**
Mount the relationship sub-router into the main assets router.

**File:** `adapters/http/api/assets/routers.py` (modify)

**Implementation:**
```python
from adapters.http.api.assets.relationship_router import relationship_router

router.include_router(
    relationship_router,
    prefix="/{asset_id}/relationships",
    tags=["asset-relationships"],
)
```

**Acceptance Criteria:**
- [x] Sub-router mounted under `/{asset_id}/relationships` prefix
- [x] Tagged as "asset-relationships" in OpenAPI docs

---

## Phase 5: Tests

### TASK-015: Unit Tests — CIRelationship Entity

**Phase:** Tests — Unit (Domain)
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Unit tests for CIRelationship entity.

**File:** `tests/unit/asset_bc/asset/domain/test_ci_relationship.py` (new)

**Test cases:**
- `test_create_generates_ulid` — id is non-empty string
- `test_create_sets_all_fields` — all fields populated correctly
- `test_create_default_description_none` — description defaults to None
- `test_update_description_returns_changes` — change dict with old/new
- `test_update_description_no_change_returns_empty` — empty dict when same value
- `test_update_description_to_none` — clearing description returns changes

**Acceptance Criteria:**
- [x] All 6 test cases pass
- [x] Tests factory create() and update_description()

---

### TASK-016: Unit Tests — CreateCIRelationshipCommandHandler

**Phase:** Tests — Unit (Commands)
**Complexity:** M
**Dependencies:** TASK-007

**Description:**
Unit tests for the create handler with all constraint validations.

**File:** `tests/unit/asset_bc/asset/application/commands/test_create_ci_relationship.py` (new)

**Test cases:**
- `test_create_success` — happy path, event recorded
- `test_self_reference_raises` — source == target → SelfReferenceError
- `test_source_not_found_raises` — source asset not found → AssetNotFoundError
- `test_target_not_found_raises` — target asset not found → AssetNotFoundError
- `test_decommissioned_target_raises` — target decommissioned → DecommissionedTargetError
- `test_duplicate_raises` — duplicate exists → DuplicateRelationshipError
- `test_event_recorded_on_source` — AssetEvent created with correct data

**Acceptance Criteria:**
- [x] All 7 test cases pass
- [x] Uses MagicMock for repositories
- [x] Verifies constraint validation order
- [x] Verifies event data structure

---

### TASK-017: Unit Tests — UpdateCIRelationshipCommandHandler

**Phase:** Tests — Unit (Commands)
**Complexity:** S
**Dependencies:** TASK-008

**Description:**
Unit tests for the update handler.

**File:** `tests/unit/asset_bc/asset/application/commands/test_update_ci_relationship.py` (new)

**Test cases:**
- `test_update_success` — description updated, saved
- `test_not_found_raises` — CIRelationshipNotFoundError
- `test_no_change_does_not_save` — same description, no save call

**Acceptance Criteria:**
- [x] All 3 test cases pass
- [x] Verifies save is only called when changes occur

---

### TASK-018: Unit Tests — DeleteCIRelationshipCommandHandler

**Phase:** Tests — Unit (Commands)
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Unit tests for the delete handler.

**File:** `tests/unit/asset_bc/asset/application/commands/test_delete_ci_relationship.py` (new)

**Test cases:**
- `test_delete_success` — relationship deleted
- `test_not_found_raises` — CIRelationshipNotFoundError
- `test_event_recorded_on_source` — AssetEvent with ci_relationship_deleted

**Acceptance Criteria:**
- [x] All 3 test cases pass
- [x] Verifies hard delete (ci_repo.delete called)
- [x] Verifies event recorded with correct data

---

### TASK-019: Integration Tests — CI Relationship Endpoints

**Phase:** Tests — Integration
**Complexity:** M
**Dependencies:** TASK-013, TASK-014

**Description:**
Integration tests for all 4 HTTP endpoints.

**File:** `tests/integration/test_ci_relationship_endpoints.py` (new)

**Test cases:**
- **POST (create):**
  - `test_create_relationship` — happy path, 201, response has enriched fields
  - `test_create_self_reference_422` — source == target
  - `test_create_duplicate_409` — same source+target+type
  - `test_create_decommissioned_target_422`
  - `test_create_target_not_found_404`
  - `test_create_event_recorded` — check AssetEvent via history endpoint
- **GET (list):**
  - `test_list_relationships` — returns both directions
  - `test_list_empty` — no relationships returns empty list
  - `test_list_includes_enriched_fields` — target/source name, serial, criticality
- **PATCH (update):**
  - `test_update_description` — happy path
  - `test_update_not_found_404`
- **DELETE:**
  - `test_delete_relationship_204` — hard delete
  - `test_delete_not_found_404`
  - `test_delete_event_recorded`

**Acceptance Criteria:**
- [x] All 14 test cases pass
- [x] Uses real DB (PostgreSQL via conftest fixtures)
- [x] Creates test assets before relationship tests
- [x] Verifies correct HTTP status codes
- [x] Verifies response schema structure

---

## Phase 6: Frontend

### TASK-020: Frontend — Dependencies Tab, Add Modal, i18n

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-014

**Description:**
Add Dependencies tab to AssetDetailPage, Add Relationship modal, and i18n translations.

**Files to modify:**
- `web/app/src/types/index.ts` — Add `CIRelationship` TypeScript interface
- `web/app/src/pages/technician/AssetDetailPage.tsx` — Add Dependencies tab
- `web/app/src/locales/en.ts` — i18n keys
- `web/app/src/locales/es.ts` — i18n keys

**TypeScript type:**
```typescript
interface CIRelationship {
  id: string;
  source_asset_id: string;
  target_asset_id: string;
  relationship_type: string;
  description: string | null;
  created_at: string;
  created_by: string;
  target_asset_name: string | null;
  target_asset_serial: string | null;
  target_asset_type: string | null;
  target_asset_criticality: string | null;
  target_asset_status: string | null;
  source_asset_name: string | null;
  source_asset_serial: string | null;
  source_asset_type: string | null;
  source_asset_criticality: string | null;
  source_asset_status: string | null;
}
```

**Dependencies tab:**
- Two sections: "Depends On" (asset is source) and "Depended On By" (asset is target)
- Each row: type icon/label, linked asset name (brand+model), serial, criticality badge, description, edit/delete actions
- "Add Relationship" button opens modal
- Delete with confirmation dialog

**Add Relationship modal:**
- Type dropdown: 5 types with display labels
- Asset search: searchable combobox querying `/api/v1/assets?search=...`
- Description: optional text field (max 500)
- Submit: POST to `/api/v1/assets/{asset_id}/relationships`

**Edit description:**
- Inline edit or small modal for description field
- PATCH to `/api/v1/assets/{asset_id}/relationships/{rel_id}`

**i18n keys (EN):**
- Relationship types: "Runs on", "Depends on", "Connected to", "Part of", "Backs up"
- Sections: "Dependencies", "Depends On", "Depended On By"
- Actions: "Add Relationship", "Edit Description", "Delete Relationship"
- Confirmation: "Are you sure you want to delete this relationship?"

**i18n keys (ES):**
- Relationship types: "Se ejecuta en", "Depende de", "Conectado a", "Parte de", "Respalda"
- Sections: "Dependencias", "Depende de", "Dependido por"
- Actions: "Agregar relación", "Editar descripción", "Eliminar relación"
- Confirmation: "¿Está seguro de que desea eliminar esta relación?"

**Acceptance Criteria:**
- [x] Dependencies tab visible on asset detail page
- [x] Two sections: upstream (source) and downstream (target)
- [x] Each row shows type label, asset name, serial, criticality badge, description
- [x] Add Relationship modal with type dropdown, asset search, description
- [x] Edit description inline or modal
- [x] Delete with confirmation dialog
- [x] All i18n keys in EN and ES
- [x] TypeScript type added to types/index.ts

---

## Phase 7: Verification

### TASK-021: Verify Implementation

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Run all verification checks.

**Checks:**
1. `npx tsc --noEmit` — TypeScript clean (0 errors)
2. `make test` — Unit tests pass (all asset_bc tests)
3. `make test-integration` — Integration tests pass (CI relationship endpoints)
4. Manual: verify OpenAPI docs show new endpoints at `/docs`

**Acceptance Criteria:**
- [x] TypeScript compilation clean
- [x] All unit tests pass
- [x] All integration tests pass
- [x] OpenAPI docs display relationship endpoints

---

## Dependency Graph

```
TASK-001 (Enum)
    │
    ├── TASK-002 (Entity) ──── TASK-015 (Unit: Entity)
    │       │
    │       ├── TASK-003 (Interface)
    │       │       │
    │       │       ├── TASK-006 (Repository) ── TASK-007 (Create Cmd) ── TASK-016 (Unit: Create)
    │       │       │                         ├── TASK-008 (Update Cmd) ── TASK-017 (Unit: Update)
    │       │       │                         ├── TASK-009 (Delete Cmd) ── TASK-018 (Unit: Delete)
    │       │       │                         └── TASK-010 (Query) ─────── (tested in integration)
    │       │       │
    │       │       └── TASK-012 (Dependencies)
    │       │
    │       └── TASK-004 (Model) ── TASK-005 (Migration)
    │
    └── TASK-011 (Schemas)

TASK-007..010, TASK-011, TASK-012 ── TASK-013 (Router) ── TASK-014 (Mount)

TASK-014 ── TASK-019 (Integration Tests)
TASK-014 ── TASK-020 (Frontend)

All ── TASK-021 (Verification)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-011
**Batch 2 (Sequential after B1):** TASK-002, TASK-004
**Batch 3 (Sequential after B2):** TASK-003, TASK-005
**Batch 4 (Parallel after B3):** TASK-006, TASK-012, TASK-015
**Batch 5 (Parallel after B4):** TASK-007, TASK-008, TASK-009, TASK-010
**Batch 6 (Parallel after B5):** TASK-013, TASK-016, TASK-017, TASK-018
**Batch 7 (Sequential after B6):** TASK-014
**Batch 8 (Parallel after B7):** TASK-019, TASK-020
**Batch 9 (After all):** TASK-021

## Final Checklist

- [x] All tasks completed
- [x] All unit tests passing
- [x] All integration tests passing
- [x] TypeScript compilation clean
- [x] i18n complete (EN + ES)
- [x] Progress tracking updated (tasks.md, slicing.md)
