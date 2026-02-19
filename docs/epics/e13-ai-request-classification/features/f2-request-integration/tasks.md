# Tasks: F2 — Request Integration

**Requirement:** [../../requirements.md](../../requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-18
**Total Tasks:** 13
**Complexity:** High

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application — ClassificationService | 1 | L |
| Application — PriorityScorer Extension | 1 | S |
| Application — CreateRequestCommand | 1 | M |
| HTTP — Router | 1 | M |
| HTTP — Dependencies | 1 | S |
| Tests — ClassificationService | 1 | M |
| Tests — PriorityScorer | 1 | S |
| Tests — CreateRequest | 1 | S |
| Tests — Integration | 1 | M |
| Verification | 1 | S |

## Phase 1: Application Layer

### TASK-001: Create ClassificationService
**Phase:** Application
**Complexity:** L
**Dependencies:** F0 (all), F1 (entity)
- [x] Create `src/request_bc/request/application/services/classification_service.py`
- [x] `ClassificationServiceResult` frozen dataclass per design
- [x] `ClassificationService` class per design:
  - `__init__(classifier, config, valid_types)`
  - `classify_request(title, description, user_type, user_subtype) -> ClassificationServiceResult`
  - Latency measurement (time.time before/after)
  - Override logic with pre-validation against VALID_SUBTYPES
  - Metadata dict construction per design schema
- [x] `build_classifier()` static factory per design
- [x] Acceptance: service returns correct results for override/no-override/failure cases

### TASK-002: Extend PriorityScorer
**Phase:** Application
**Complexity:** S
**Dependencies:** None
- [x] Edit `src/request_bc/request/application/services/priority_scorer.py`
- [x] Add `ai_priority_hint: int = 0` parameter to `compute()`
- [x] Add `ai_hint_w` to weight calculation and `raw_score`
- [x] Add `"ai_hint_weight"` to breakdown dict
- [x] Acceptance: existing callers unaffected (default=0), new parameter works

### TASK-003: Extend CreateRequestCommand
**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-002
- [x] Edit `src/request_bc/request/application/commands/create_request.py`
- [x] Add `ai_priority_hint: int = 0` to command dataclass
- [x] Add `ai_classification: Optional[dict] = None` to command dataclass
- [x] Handler: pass `ai_priority_hint` to `PriorityScorer.compute()`
- [x] Handler: merge `ai_classification` into `request.data` under key `"ai_classification"`
- [x] Acceptance: command handler stays clean, no AI infrastructure in handler

## Phase 2: HTTP Layer

### TASK-004: Update router
**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-001, TASK-003
- [x] Edit `adapters/http/api/requests/routers.py`
- [x] Inject `classification_config_repo` dependency in create endpoint
- [x] Look up config, build classifier via `ClassificationService.build_classifier()`
- [x] Call `ClassificationService.classify_request()`
- [x] Pass resolved values to `CreateRequestCommand` per design
- [x] Acceptance: create request works with and without AI classification

### TASK-005: Add dependency
**Phase:** HTTP
**Complexity:** S
**Dependencies:** F1 (repository)
- [x] Edit `adapters/http/api/requests/dependencies.py`
- [x] Add `get_classification_config_repo(db) -> ClassificationConfigRepository`
- [x] Acceptance: dependency injectable in router

## Phase 3: Tests

### TASK-006: Unit tests — ClassificationService
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001
- [x] Create `tests/unit/request_bc/request/application/services/test_classification_service.py`
- [x] Test: confident + type differs → override, user_original stored
- [x] Test: confident + same type → no override, ai_used=True
- [x] Test: below threshold → no override
- [x] Test: classifier returns None → fallback, ai_used=False
- [x] Test: invalid type suggestion → no override
- [x] Test: invalid subtype suggestion → no override
- [x] Test: latency recorded
- [x] Test: build_classifier OpenAI
- [x] Test: build_classifier Groq
- [x] Acceptance: ~9 tests pass

### TASK-007: Unit tests — PriorityScorer
**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-002
- [x] Edit `tests/unit/request_bc/request/application/services/test_priority_scorer.py`
- [x] Test: ai_priority_hint=0 → ai_hint_weight=0
- [x] Test: ai_priority_hint=2 → raw_score +2
- [x] Test: ai_priority_hint=-1 → raw_score -1
- [x] Test: pushes medium → urgent
- [x] Acceptance: ~4 new tests pass

### TASK-008: Unit tests — CreateRequest
**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-003
- [x] Edit `tests/unit/request_bc/request/application/commands/test_commands.py`
- [x] Test: ai_priority_hint passed to scorer
- [x] Test: ai_priority_hint=0 default → scorer unaffected
- [x] Test: ai_classification merged into request.data
- [x] Test: ai_classification=None → no key in data
- [x] Acceptance: ~4 new tests pass

### TASK-009: Integration tests
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-004, TASK-005
- [x] Edit `tests/integration/test_requests_endpoints.py`
- [x] Test: create with AI enabled (mock adapter) → metadata in response
- [x] Test: create without config → normal, no ai_classification
- [x] Test: create with AI override → type/subtype overridden
- [x] Acceptance: ~3 new tests pass

## Verification

### TASK-010: Verify F2
- [x] All unit tests pass: `python -m pytest tests/unit/request_bc/ -v`
- [x] Integration tests pass: `make test-integration`
- [x] No lint errors: `make lint`

## Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F2 status to Done
