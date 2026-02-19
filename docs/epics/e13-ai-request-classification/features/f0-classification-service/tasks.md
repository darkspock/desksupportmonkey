# Tasks: F0 — Classification Service

**Requirement:** [../../requirements.md](../../requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-18
**Total Tasks:** 14
**Complexity:** Medium

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Port | 1 | S |
| Domain — Value Object | 1 | S |
| Domain — Service | 1 | M |
| Infrastructure — Adapters | 2 | M |
| Tests — Orchestrator | 1 | M |
| Tests — Adapters | 1 | M |
| Verification | 1 | S |

## Phase 1: Domain Layer

### TASK-001: Add RequestClassifierPort to ports.py
**Phase:** Domain
**Complexity:** S
**Dependencies:** None
- [x] Edit `src/request_bc/request/application/ports.py`
- [x] Add `RequestClassifierPort(ABC)` with `classify()` method per design
- [x] Keep existing `UserLookup` port untouched
- [x] Acceptance: port class importable, method signature matches design

### TASK-002: Create ClassificationResult dataclass
**Phase:** Domain
**Complexity:** S
**Dependencies:** None
- [x] Create `src/request_bc/request/application/services/request_classifier.py`
- [x] Add `@dataclass(frozen=True) ClassificationResult` with fields per design: `type`, `subtype`, `priority_hint`, `confidence`
- [x] Acceptance: dataclass importable, immutable

### TASK-003: Create ClassificationOrchestrator
**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002
- [x] Add `ClassificationOrchestrator` to `request_classifier.py`
- [x] `__init__(classifier: RequestClassifierPort)`
- [x] `classify()` method: calls classifier, validates result against `valid_types`
- [x] Validation: type in valid_types keys, subtype valid for type, empty-subtypes-list handling
- [x] On any exception: log warning, return `None`
- [x] Acceptance: orchestrator catches all exceptions, returns None on invalid results

## Phase 2: Infrastructure Layer

### TASK-004: Create OpenAI classifier adapter
**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-001, TASK-002
- [x] Create `src/request_bc/request/infrastructure/ai/__init__.py`
- [x] Create `src/request_bc/request/infrastructure/ai/openai_classifier.py`
- [x] `OpenAIRequestClassifier(RequestClassifierPort)` per design
- [x] `__init__(api_key, model="gpt-4o-mini", timeout_seconds=10)`
- [x] No API key → return None
- [x] Use `openai.OpenAI(api_key, timeout=timeout_seconds)` — deferred import
- [x] Build system + user messages per design prompt structure
- [x] `temperature=0`, `max_tokens=200`, JSON mode
- [x] Parse JSON response → `ClassificationResult`
- [x] On exception: log warning, return None
- [x] Acceptance: adapter returns valid ClassificationResult or None

### TASK-005: Create Groq classifier adapter
**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-001, TASK-002
- [x] Create `src/request_bc/request/infrastructure/ai/groq_classifier.py`
- [x] `GroqRequestClassifier(RequestClassifierPort)` per design
- [x] Same as OpenAI with `base_url="https://api.groq.com/openai/v1"`, default model `"llama-3.1-8b-instant"`
- [x] Acceptance: adapter returns valid ClassificationResult or None

## Phase 3: Tests

### TASK-006: Unit tests — Orchestrator
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-003
- [x] Create `tests/unit/request_bc/request/application/services/__init__.py` (if not exists)
- [x] Create `tests/unit/request_bc/request/application/services/test_request_classifier.py`
- [x] Test: successful classification returns result
- [x] Test: invalid type → None
- [x] Test: invalid subtype for type → None
- [x] Test: subtype for empty-subtypes type → None
- [x] Test: classifier exception → None
- [x] Test: confidence and priority_hint pass through
- [x] Test: ClassificationResult dataclass fields
- [x] Acceptance: ~7 tests pass

### TASK-007: Unit tests — Adapters
**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-004, TASK-005
- [x] Create `tests/unit/request_bc/request/infrastructure/__init__.py` (if not exists)
- [x] Create `tests/unit/request_bc/request/infrastructure/ai/__init__.py`
- [x] Create `tests/unit/request_bc/request/infrastructure/ai/test_adapters.py`
- [x] OpenAI: no API key → None
- [x] OpenAI: successful response → ClassificationResult
- [x] OpenAI: malformed JSON → None
- [x] OpenAI: API error → None
- [x] Groq: same 4 tests
- [x] Mock `openai.OpenAI` via `unittest.mock.patch`
- [x] Acceptance: ~8 tests pass

## Verification

### TASK-008: Verify F0
- [x] All tests pass: `python -m pytest tests/unit/request_bc/request/application/services/test_request_classifier.py tests/unit/request_bc/request/infrastructure/ai/test_adapters.py -v`
- [x] No lint errors: `make lint`

## Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F0 status to Done
