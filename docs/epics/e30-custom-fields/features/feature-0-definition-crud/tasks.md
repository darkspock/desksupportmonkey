# Implementation Tasks: F0 — Definition CRUD

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-24
**Total Tasks:** 15
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Repository Interface | 1 | S |
| Infrastructure - Migration | 1 | S |
| Infrastructure - Model | 1 | S |
| Infrastructure - Repository | 1 | M |
| Application - DTOs | 1 | S |
| Application - Commands | 1 | M |
| Application - Queries | 1 | S |
| HTTP - Schemas + Dependencies + Router | 1 | M |
| Collateral - app.py + conftest | 1 | S |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Frontend - Admin page + sidebar + router + i18n | 1 | L |

---

## Phase 1: Domain Layer

### TASK-001: Create Enums

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**File:** `src/custom_field_bc/definition/domain/enums.py`

**Implementation:**
```python
from enum import Enum

class EntityType(str, Enum):
    ASSET = "asset"
    REQUEST = "request"
    INCIDENT = "incident"

class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
```

Also create `__init__.py` files for:
- `src/custom_field_bc/__init__.py`
- `src/custom_field_bc/definition/__init__.py`
- `src/custom_field_bc/definition/domain/__init__.py`
- `src/custom_field_bc/definition/application/__init__.py`
- `src/custom_field_bc/definition/application/commands/__init__.py`
- `src/custom_field_bc/definition/application/queries/__init__.py`
- `src/custom_field_bc/definition/application/services/__init__.py`
- `src/custom_field_bc/definition/infrastructure/__init__.py`

**Acceptance Criteria:**
- [ ] `EntityType` enum with 3 values
- [ ] `FieldType` enum with 6 values
- [ ] Both inherit from `str, Enum`
- [ ] All `__init__.py` files created

---

### TASK-002: Create Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**File:** `src/custom_field_bc/definition/domain/exceptions.py`

**Implementation:**
```python
class FieldDefinitionNotFoundError(Exception): ...
class DuplicateFieldKeyError(Exception): ...
class MaxFieldsExceededError(Exception): ...
class InvalidFieldTypeError(Exception): ...
class OptionsRequiredError(Exception): ...
```

**Acceptance Criteria:**
- [ ] 5 exception classes
- [ ] All inherit from `Exception`
- [ ] Meaningful default messages with `__init__` accepting context params

---

### TASK-003: Create CustomFieldDefinition Entity

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**File:** `src/custom_field_bc/definition/domain/entities.py`

**Implementation:**
- `@dataclass` class with all fields from design
- `create()` classmethod: generates ULID, calls `_slugify()`, validates options
- `_slugify(label)` static method: lowercase, spaces→underscores, strip non-alphanumeric (keep underscores), max 50 chars
- `update(label, description, required, options, visible_to_employees)`: updates mutable fields, validates options if select type
- `deactivate()`: sets `is_active = False`
- `activate()`: sets `is_active = True`
- Validation: `options` required for select/multi_select, forbidden for other types. Raises `OptionsRequiredError`.

**Acceptance Criteria:**
- [ ] All fields from design
- [ ] `create()` factory method with slug generation
- [ ] `_slugify()` handles: spaces, special chars, unicode, max length
- [ ] `update()` validates options consistency
- [ ] `deactivate()` / `activate()` toggle `is_active`
- [ ] Options validation on create and update

---

### TASK-004: Create Repository Interface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/custom_field_bc/definition/domain/repository.py`

**Implementation:**
```python
from abc import ABC, abstractmethod

class CustomFieldDefinitionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, definition: CustomFieldDefinition) -> None: ...
    @abstractmethod
    def find_by_id(self, id: str, company_id: str) -> Optional[CustomFieldDefinition]: ...
    @abstractmethod
    def find_by_entity_type(self, company_id: str, entity_type: str) -> list[CustomFieldDefinition]: ...
    @abstractmethod
    def find_active_by_entity_type(self, company_id: str, entity_type: str) -> list[CustomFieldDefinition]: ...
    @abstractmethod
    def count_by_entity_type(self, company_id: str, entity_type: str) -> int: ...
    @abstractmethod
    def has_field_key(self, company_id: str, entity_type: str, field_key: str) -> bool: ...
    @abstractmethod
    def delete(self, id: str) -> None: ...
    @abstractmethod
    def bulk_update_sort_order(self, updates: list[tuple[str, int]]) -> None: ...
```

**Acceptance Criteria:**
- [ ] ABC class with 8 abstract methods
- [ ] Method signatures match design exactly
- [ ] Uses domain entities in signatures

---

## Phase 2: Infrastructure Layer

### TASK-005: Create Migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**File:** `alembic/versions/j1k2l3m4n5o6_create_custom_field_definitions.py`

**Implementation:**
Create `custom_field_definitions` table with all columns, indexes, and unique constraint as specified in design. Include `upgrade()` and `downgrade()`.

**Acceptance Criteria:**
- [ ] All columns from design schema
- [ ] Index on `(company_id, entity_type)`
- [ ] Unique constraint on `(company_id, entity_type, field_key)`
- [ ] Foreign key to `companies(id)`
- [ ] `downgrade()` drops table

---

### TASK-006: Create SQLAlchemy Model

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**File:** `src/custom_field_bc/definition/infrastructure/models.py`

**Implementation:**
`CustomFieldDefinitionModel` with `ULIDMixin`, `TimestampMixin`, `Base`. All columns using `Mapped[type]` annotations. `__table_args__` with indexes and unique constraint.

**Acceptance Criteria:**
- [ ] All columns with `Mapped[type]` + `mapped_column()`
- [ ] `__tablename__ = "custom_field_definitions"`
- [ ] Indexes and unique constraint in `__table_args__`
- [ ] `visible_to_employees` column with `server_default="true"`

---

### TASK-007: Create Repository Implementation

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-004, TASK-006

**File:** `src/custom_field_bc/definition/infrastructure/repository.py`

**Implementation:**
- Implements `CustomFieldDefinitionRepositoryInterface`
- `__init__(self, session: Session)`
- `_entity_to_model()` and `_model_to_entity()` converters
- All 8 methods implemented using SQLAlchemy 2.0 select/where/execute
- `bulk_update_sort_order`: iterate updates and set sort_order per id
- `session.flush()` after writes

**Acceptance Criteria:**
- [ ] All 8 interface methods implemented
- [ ] Bidirectional entity↔model conversion
- [ ] `find_by_entity_type` sorts by `sort_order`
- [ ] `find_active_by_entity_type` filters `is_active=True` and sorts
- [ ] `has_field_key` returns bool
- [ ] `count_by_entity_type` returns int

---

## Phase 3: Application Layer

### TASK-008: Create DTOs

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/custom_field_bc/definition/application/dtos.py`

**Implementation:**
`FieldDefinitionDto` dataclass with all fields from design.

**Acceptance Criteria:**
- [ ] All fields matching entity + timestamps
- [ ] `@dataclass` class

---

### TASK-009: Create Commands

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004, TASK-008

**Files:**
- `src/custom_field_bc/definition/application/commands/create_definition.py`
- `src/custom_field_bc/definition/application/commands/update_definition.py`
- `src/custom_field_bc/definition/application/commands/delete_definition.py`
- `src/custom_field_bc/definition/application/commands/deactivate_definition.py`
- `src/custom_field_bc/definition/application/commands/activate_definition.py`
- `src/custom_field_bc/definition/application/commands/reorder_definitions.py`

**Implementation per command:**
- `@dataclass class XxxCommand(Command)` with required fields
- `class XxxCommandHandler(CommandHandler[XxxCommand])` with `__init__(repo)` and `handle(command)`
- **Create**: check `count_by_entity_type < 20`, check `has_field_key` uniqueness, call `CustomFieldDefinition.create()`, override `id`, save
- **Update**: find by id, call `entity.update()`, save
- **Delete**: find by id (verify exists), call `repo.delete(id)`
- **Deactivate/Activate**: find by id, call `entity.deactivate()`/`activate()`, save
- **Reorder**: validate all ids belong to same company+entity_type, call `repo.bulk_update_sort_order()`

**Acceptance Criteria:**
- [ ] 6 command + handler pairs
- [ ] All inherit from `Command` / `CommandHandler`
- [ ] Create validates max 20 fields and slug uniqueness
- [ ] Create pre-generates ID in command
- [ ] Domain exceptions raised on validation failures

---

### TASK-010: Create Queries

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004, TASK-008

**Files:**
- `src/custom_field_bc/definition/application/queries/list_definitions.py`
- `src/custom_field_bc/definition/application/queries/get_definition.py`

**Implementation:**
- **List**: `ListFieldDefinitionsQuery(company_id, entity_type)` → `list[FieldDefinitionDto]`
- **Get**: `GetFieldDefinitionQuery(definition_id, company_id)` → `FieldDefinitionDto`, raises `FieldDefinitionNotFoundError`

**Acceptance Criteria:**
- [ ] 2 query + handler pairs
- [ ] All inherit from `Query` / `QueryHandler`
- [ ] List returns sorted by `sort_order`
- [ ] Get raises 404 exception if not found

---

## Phase 4: HTTP Layer

### TASK-011: Create Schemas + Dependencies + Router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-009, TASK-010

**Files:**
- `adapters/http/api/custom_fields/__init__.py`
- `adapters/http/api/custom_fields/schemas.py`
- `adapters/http/api/custom_fields/dependencies.py`
- `adapters/http/api/custom_fields/routers.py`

**Schemas:** `CreateFieldDefinitionRequest`, `UpdateFieldDefinitionRequest`, `ReorderRequest`, `FieldDefinitionResponse` — as specified in design.

**Dependencies:** `get_cf_definition_repo(db=Depends(get_db))` returning `CustomFieldDefinitionRepository(db)`.

**Router:** `APIRouter(prefix="/api/v1/custom-fields", tags=["custom-fields"])`. 8 endpoints, all guarded by `require_plan_feature("custom_fields")` + `require_role(UserRole.ADMIN)`. Pre-generate ID with `str(ulid.new())` on create. Catch domain exceptions → HTTPException (409 for duplicate, 422 for max fields, 404 for not found).

**Acceptance Criteria:**
- [ ] 8 endpoints matching design
- [ ] All endpoints require Enterprise plan (402 test)
- [ ] All endpoints require admin role
- [ ] Proper exception handling → HTTP status codes
- [ ] `_to_response()` helper for DTO→dict

---

## Phase 5: Collateral

### TASK-012: Register Router + Models

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-011

**Files:**
- `app.py` — add `from adapters.http.api.custom_fields.routers import router as custom_fields_router` + `application.include_router(custom_fields_router)`
- `tests/conftest.py` — add `from src.custom_field_bc.definition.infrastructure.models import CustomFieldDefinitionModel`

**Acceptance Criteria:**
- [ ] Router registered in app.py
- [ ] Model imported in conftest.py

---

## Phase 6: Tests

### TASK-013: Unit Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-009, TASK-010

**Files:**
- `tests/unit/custom_field_bc/definition/domain/test_entities.py`
- `tests/unit/custom_field_bc/definition/application/commands/test_create_definition.py`
- `tests/unit/custom_field_bc/definition/application/commands/test_update_definition.py`
- `tests/unit/custom_field_bc/definition/application/commands/test_delete_definition.py`
- `tests/unit/custom_field_bc/definition/application/commands/test_deactivate_activate.py`
- `tests/unit/custom_field_bc/definition/application/commands/test_reorder_definitions.py`
- `tests/unit/custom_field_bc/definition/application/queries/test_queries.py`

**Test cases (entity):**
- `create()` generates valid slug from label
- `_slugify()` edge cases: special chars, unicode, max length, leading/trailing spaces
- `create()` with select type requires options
- `create()` with text type rejects options
- `update()` validates options consistency
- `deactivate()` / `activate()` toggling

**Test cases (commands):**
- Create: success, max 20 exceeded, duplicate slug
- Update: success, not found
- Delete: success, not found
- Deactivate/Activate: success, not found
- Reorder: success

**Test cases (queries):**
- List: returns sorted by sort_order
- Get: success, not found

Create `__init__.py` files for test directories.

**Acceptance Criteria:**
- [ ] Entity creation and validation tests
- [ ] Slugify edge case tests
- [ ] All 6 command handler tests with MagicMock repo
- [ ] Both query handler tests
- [ ] `make test` passes

---

### TASK-014: Integration Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-012

**File:** `tests/integration/test_custom_fields_endpoints.py`

**Test cases:**
- POST create definition → 201
- POST create with non-Enterprise plan → 402
- POST create 21st field → 422 (max exceeded)
- POST create duplicate slug → 409
- GET list by entity_type → 200 + sorted
- GET single by id → 200
- GET single not found → 404
- PUT update → 200
- DELETE → 204
- POST deactivate → 200
- POST activate → 200
- PUT reorder → 200

**Acceptance Criteria:**
- [ ] All 8 endpoints tested
- [ ] Plan gating test (402)
- [ ] Boundary tests (max 20, duplicate key)
- [ ] `make test-integration` passes

---

## Phase 7: Frontend

### TASK-015: Admin Page + Sidebar + Router + i18n

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-011

**Files:**
- `web/app/src/pages/admin/CustomFieldsPage.tsx` — main admin page
- `web/app/src/router.tsx` — add `/custom-fields` route
- `web/app/src/components/layout/Sidebar.tsx` — add nav item under Settings
- `web/app/src/types/index.ts` — add `CustomFieldDefinition` interface
- `web/app/src/locales/en.ts` — add ~25 keys
- `web/app/src/locales/es.ts` — add ~25 keys

**CustomFieldsPage implementation:**
- 3 tabs: Assets | Requests | Incidents (active tab stored in state)
- Table showing definitions for active tab: label, type, required badge, active/inactive badge, sort arrows, edit/delete buttons
- "Add Field" button opens modal form
- Modal form: label, type dropdown, description, required checkbox, visible_to_employees checkbox
- Conditional: options list editor when type is select/multi_select (add/remove option inputs)
- Edit modal: pre-filled, type disabled
- Delete: confirmation dialog with warning
- Deactivate/Activate: toggle button
- Reorder: up/down arrow buttons, calls PUT reorder with new order

**Acceptance Criteria:**
- [ ] Tabs switch between entity types
- [ ] Create field modal with all field types
- [ ] Options editor for select/multi_select types
- [ ] Edit modal (type immutable)
- [ ] Delete with confirmation
- [ ] Deactivate/activate toggle
- [ ] Reorder arrows
- [ ] Plan gate: page shows upgrade prompt for non-Enterprise
- [ ] All text through i18n
- [ ] `npx tsc --noEmit` passes

---

## Dependency Graph

```
TASK-001 (Enums) ──┐
TASK-002 (Exceptions)──┤
                       ├── TASK-003 (Entity) ──┬── TASK-004 (Repo Interface) ──┐
                       │                       ├── TASK-005 (Migration) ──── TASK-006 (Model) ──┤
                       │                       └── TASK-008 (DTOs)                              │
                       │                                                                        │
                       │                       ┌── TASK-007 (Repo Impl) ◄──────────────────────┘
                       │                       │
                       └── TASK-009 (Commands) ◄┤
                           TASK-010 (Queries) ◄─┤
                                                │
                           TASK-011 (HTTP) ◄────┘
                                │
                           TASK-012 (Collateral) ──── TASK-014 (Integration Tests)
                                │
                           TASK-013 (Unit Tests)
                           TASK-015 (Frontend)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002
**Batch 2:** TASK-003
**Batch 3 (Parallel):** TASK-004, TASK-005, TASK-008
**Batch 4 (Parallel):** TASK-006, TASK-007
**Batch 5 (Parallel):** TASK-009, TASK-010
**Batch 6:** TASK-011
**Batch 7 (Parallel):** TASK-012, TASK-013, TASK-015
**Batch 8:** TASK-014

## Final Checklist

- [x] All 15 tasks completed
- [x] `make test` passes (unit) — 32/32 pass
- [ ] `make test-integration` passes (requires Docker)
- [x] `make lint` passes (flake8 clean)
- [x] `npx tsc --noEmit` passes (frontend)
- [ ] Plan gating verified (402 for non-Enterprise) — covered in integration tests
