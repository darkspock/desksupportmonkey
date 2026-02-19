# Tasks: F1 — Company Configuration

**Requirement:** [../../requirements.md](../../requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-18
**Total Tasks:** 18
**Complexity:** Medium

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Entity | 1 | S |
| Domain — Repository Interface | 1 | S |
| Infrastructure — Model | 1 | M |
| Infrastructure — Migration | 1 | M |
| Infrastructure — Repository | 1 | M |
| Application — Save Command | 1 | M |
| Application — Get Query + DTO | 1 | M |
| HTTP — Schemas | 1 | S |
| HTTP — Router | 1 | M |
| HTTP — Dependencies | 1 | S |
| Configuration — app.py | 1 | S |
| Tests — Unit | 1 | M |
| Tests — Integration | 1 | M |
| Verification | 1 | S |

## Phase 1: Domain Layer

### TASK-001: Create entity
**Phase:** Domain
**Complexity:** S
**Dependencies:** None
- [x] Create `src/company_bc/classification_config/__init__.py`
- [x] Create `src/company_bc/classification_config/domain/__init__.py`
- [x] Create `src/company_bc/classification_config/domain/entities.py`
- [x] `@dataclass CompanyClassificationConfig` with fields per design
- [x] Import `AIProvider` from `src.company_bc.assignment_config.domain.enums`
- [x] `provider: AIProvider` (enum, not str)
- [x] Factory method `create()` per design
- [x] Acceptance: entity importable, factory works

### TASK-002: Create repository interface
**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001
- [x] Create `src/company_bc/classification_config/domain/repository.py`
- [x] `ClassificationConfigRepositoryInterface(ABC)` with `save()`, `find_by_company()`
- [x] Acceptance: interface importable

## Phase 2: Infrastructure Layer

### TASK-003: Create SQLAlchemy model
**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-001
- [x] Create `src/company_bc/classification_config/infrastructure/__init__.py`
- [x] Create `src/company_bc/classification_config/infrastructure/models.py`
- [x] `ClassificationConfigModel(ULIDMixin, TimestampMixin, Base)` per design
- [x] All columns use `Mapped[type]` annotations (2.0 style)
- [x] `UniqueConstraint("company_id")`
- [x] Acceptance: model importable, matches migration schema

### TASK-004: Create migration
**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-003
- [x] Create `alembic/versions/xxx_create_classification_config.py`
- [x] Create `company_classification_configs` table per design SQL schema
- [x] Acceptance: migration applies cleanly with `make db-upgrade`

### TASK-005: Create repository implementation
**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002, TASK-003
- [x] Create `src/company_bc/classification_config/infrastructure/repository.py`
- [x] `ClassificationConfigRepository(ClassificationConfigRepositoryInterface)`
- [x] Upsert pattern: check existing by company_id, update or insert
- [x] `_to_entity()` static method — reconstruct `AIProvider(model.provider)`
- [x] Follow `AssignmentConfigRepository` pattern
- [x] Acceptance: save/find_by_company work correctly

## Phase 3: Application Layer

### TASK-006: Create save command
**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-001, TASK-002
- [x] Create `src/company_bc/classification_config/application/__init__.py`
- [x] Create `src/company_bc/classification_config/application/commands/__init__.py`
- [x] Create `src/company_bc/classification_config/application/commands/save_config.py`
- [x] `SaveClassificationConfigCommand(Command)` + `SaveClassificationConfigCommandHandler(CommandHandler[...])` per design
- [x] Validate provider, confidence_threshold, timeout_seconds
- [x] Acceptance: handler creates/updates config, raises on invalid input

### TASK-007: Create get query + DTO
**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-001, TASK-002
- [x] Create `src/company_bc/classification_config/application/queries/__init__.py`
- [x] Create `src/company_bc/classification_config/application/queries/get_config.py`
- [x] `GetClassificationConfigQuery(Query)` + handler per design
- [x] Create `ClassificationConfigDTO` dataclass per design
- [x] Handler returns `Optional[ClassificationConfigDTO]` (not entity — Rule #2)
- [x] Acceptance: returns DTO when config exists, None when not

## Phase 4: HTTP Layer

### TASK-008: Create schemas
**Phase:** HTTP
**Complexity:** S
**Dependencies:** None
- [x] Create `adapters/http/api/settings/classification_schemas.py`
- [x] `SaveClassificationConfigRequest(BaseModel)` with field validations per design
- [x] `ClassificationConfigResponse(BaseModel)` per design
- [x] Acceptance: schemas validate input correctly

### TASK-009: Create dependencies
**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-005
- [x] Create `adapters/http/api/settings/classification_dependencies.py`
- [x] `get_classification_config_repo(db) -> ClassificationConfigRepository`
- [x] Acceptance: factory returns valid repo instance

### TASK-010: Create router
**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-006, TASK-007, TASK-008, TASK-009
- [x] Create `adapters/http/api/settings/classification_router.py`
- [x] `PUT /request-classification` — admin only, catches domain exceptions
- [x] `GET /request-classification` — admin only
- [x] Follow same pattern as assignment-ai endpoints
- [x] Acceptance: endpoints return correct responses, non-admin gets 403

### TASK-011: Register router in app.py
**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-010
- [x] Edit `app.py`
- [x] Import: `from adapters.http.api.settings.classification_router import router as classification_settings_router`
- [x] Add: `application.include_router(classification_settings_router)`
- [x] Acceptance: endpoints accessible at correct paths

## Phase 5: Tests

### TASK-012: Unit tests
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-006, TASK-007
- [x] Create `tests/unit/company_bc/classification_config/__init__.py`
- [x] Create `tests/unit/company_bc/classification_config/test_commands.py`
- [x] Save: creates new, updates existing, invalid provider, invalid threshold, invalid timeout
- [x] Get: returns DTO when found, returns None when not
- [x] Acceptance: ~7 tests pass

### TASK-013: Integration tests
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-010, TASK-011
- [x] Create `tests/integration/test_classification_config_endpoints.py`
- [x] PUT: admin saves → 200, non-admin → 403, invalid provider → 422, invalid threshold → 422
- [x] GET: returns config → 200, no config → 200 null, non-admin → 403
- [x] Acceptance: ~7 tests pass

## Verification

### TASK-014: Verify F1
- [x] Unit tests pass: `python -m pytest tests/unit/company_bc/classification_config/ -v`
- [x] Integration tests pass: `make test-integration`
- [x] Migration applies cleanly: `make db-upgrade`
- [x] No lint errors: `make lint`

## Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F1 status to Done
