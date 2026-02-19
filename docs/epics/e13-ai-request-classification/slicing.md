# Slicing: E13 - AI Request Classification

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 4

## Slicing Rationale

E13 follows a natural bottom-up progression: the classification service (F0) is a pure domain + adapter layer with no side effects — it receives text and returns structured classification. Company configuration (F1) provides the CRUD for per-company AI settings. Request integration (F2) hooks classification into the creation flow, extending priority scoring and storing metadata. Frontend (F3) exposes configuration and classification results. Each feature is independently testable and deployable.

## Dependency Graph

```text
F0: Classification Service (domain + AI adapters + port)
  └── F1: Company Configuration (CRUD, migration, API)
        └── F2: Request Integration (hook into creation, scoring extension)
              └── F3: Frontend UX (admin settings, classification display)
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Classification Service | US-E13-001 (partial) | Medium | E11 (adapter pattern) | Done |
| F1 | Company Configuration | US-E13-002 | Medium | F0 | Done |
| F2 | Request Integration | US-E13-001, US-E13-004 | High | F0, F1, E12 | Done |
| F3 | Frontend UX | US-E13-002, US-E13-003, US-E13-004 | Medium | F0, F1, F2 | Done |

---

## F0: Classification Service

**Scope:** Create the classification domain, AI adapters (OpenAI + Groq), and the orchestration service. Pure logic layer — no database, no HTTP endpoints, no request integration yet.

### Domain Changes
- Add `RequestClassifierPort` abstract interface to `src/request_bc/request/application/ports.py`
- Create classification result value object and orchestration service in `src/request_bc/request/application/services/`
- Create OpenAI and Groq adapters implementing the port in `src/request_bc/request/infrastructure/ai/`

### New Types
- `ClassificationResult`: type, subtype (nullable), priority_hint (-1 to +2), confidence (0.0–1.0)
- `RequestClassifierPort`: abstract base with `classify(title, description, valid_types) -> ClassificationResult`

### AI Adapters
- `OpenAIRequestClassifier(RequestClassifierPort)`: Uses `openai` client, JSON mode, structured prompt
- `GroqRequestClassifier(RequestClassifierPort)`: Uses OpenAI client pointed to Groq endpoint, same prompt structure

### Tests
- Unit: classification result parsing, orchestrator logic, adapter error handling, type/subtype validation
- Mock tests for OpenAI/Groq adapters
- ~15 tests

### Files

| File | Action |
|------|--------|
| `src/request_bc/request/application/ports.py` | Edit — add RequestClassifierPort |
| `src/request_bc/request/application/services/request_classifier.py` | Create — ClassificationResult, orchestrator |
| `src/request_bc/request/infrastructure/ai/__init__.py` | Create |
| `src/request_bc/request/infrastructure/ai/openai_classifier.py` | Create — OpenAI adapter |
| `src/request_bc/request/infrastructure/ai/groq_classifier.py` | Create — Groq adapter |
| `tests/unit/request_bc/request/application/services/test_request_classifier.py` | Create |
| `tests/unit/request_bc/request/infrastructure/ai/test_adapters.py` | Create |

---

## F1: Company Configuration

**Scope:** CRUD for per-company AI classification configuration. Database table, domain entity, commands/queries, API endpoints. Same pattern as E11's `company_assignment_ai_configs`.

### Domain Changes
- Create `src/company_bc/classification_config/` subdomain
- Entity: `CompanyClassificationConfig(id, company_id, is_enabled, provider, model, confidence_threshold, prompt_template, timeout_seconds, timestamps)`
- Repository interface: `ClassificationConfigRepositoryInterface`

### Infrastructure
- SQLAlchemy model: `ClassificationConfigModel` in table `company_classification_configs`
- Migration: create `company_classification_configs` table
- Repository: `ClassificationConfigRepository`

### Application Layer
- `SaveClassificationConfigCommand` + handler
- `GetClassificationConfigQuery` + handler

### API Endpoints
- `PUT /api/v1/settings/request-classification` — save/update config (admin only)
- `GET /api/v1/settings/request-classification` — retrieve config (admin only)

### Tests
- Unit: save command handler (create + update), get query handler, validation (threshold range, provider values)
- Integration: PUT + GET endpoints, admin-only access
- ~14 tests

### Files

| File | Action |
|------|--------|
| `src/company_bc/classification_config/` | Create — full subdomain structure |
| `src/company_bc/classification_config/domain/entities.py` | Create |
| `src/company_bc/classification_config/domain/repository.py` | Create — interface |
| `src/company_bc/classification_config/infrastructure/models.py` | Create — SQLAlchemy model |
| `src/company_bc/classification_config/infrastructure/repository.py` | Create — implementation |
| `src/company_bc/classification_config/application/commands/save_config.py` | Create |
| `src/company_bc/classification_config/application/queries/get_config.py` | Create |
| `alembic/versions/xxx_create_classification_config.py` | Create — migration |
| `adapters/http/api/settings/` | Edit or create — classification endpoints + schemas |
| `app.py` | Edit — register router |
| `tests/unit/company_bc/classification_config/test_commands.py` | Create |
| `tests/integration/test_classification_config_endpoints.py` | Create |

---

## F2: Request Integration

**Scope:** Hook the classification service into request creation. Extend `PriorityScorer` with AI hint weight. Store classification metadata on request. Override logic.

### Application Service
- Create `ClassificationService` to encapsulate classification orchestration, override logic, metadata building
- Business logic: build adapter, call classify, measure latency, evaluate confidence, decide override, validate type/subtype

### PriorityScorer Extension
- Add `ai_priority_hint: int = 0` parameter to `compute()`
- Add `ai_hint_weight` to scoring formula and breakdown dict

### Command Changes
- Extend `CreateRequestCommand` with resolved classification values
- Handler: pass AI hint to scorer, merge classification metadata into `request.data`

### Router Changes
- Look up classification config, call `ClassificationService`, pass resolved values to command

### Tests
- Unit: classification service (override, no override, fallback, validation), priority scorer extension, command handler
- Integration: create request with/without AI classification
- ~16 tests

### Files

| File | Action |
|------|--------|
| `src/request_bc/request/application/services/classification_service.py` | Create |
| `src/request_bc/request/application/services/priority_scorer.py` | Edit — add ai_priority_hint |
| `src/request_bc/request/application/commands/create_request.py` | Edit — add classification fields |
| `adapters/http/api/requests/routers.py` | Edit — call ClassificationService |
| `adapters/http/api/requests/dependencies.py` | Edit — add classification config repo |
| `tests/unit/request_bc/request/application/services/test_classification_service.py` | Create |
| `tests/unit/request_bc/request/application/services/test_priority_scorer.py` | Edit |
| `tests/unit/request_bc/request/application/commands/test_commands.py` | Edit |
| `tests/integration/test_requests_endpoints.py` | Edit |

---

## F3: Frontend UX

**Scope:** Admin settings page for classification configuration. Classification result display on request detail page. Updated priority scoring card with AI hint weight.

### Pages/Components

1. **Classification Settings Page** — CREATE
   - Enable/disable toggle, provider selector, model input, confidence threshold, prompt template, timeout
   - Save/load via settings API endpoints
   - Admin only

2. **RequestDetailPage** — EDIT
   - Add "AI Classification" card (when `request.data.ai_classification` exists, technician+ only)
   - Shows: AI suggested type + subtype, confidence %, override flag, user original
   - Badge: "AI Classified" when AI was used
   - Update priority scoring card to show `ai_hint_weight`

### Routing
- Add route: `settings/request-classification` → `ClassificationSettingsPage`

### Sidebar
- Add nav item: "Request Classification" under Management section (admin only)

### i18n
- ~30 keys per language (EN + ES)

### Tests
- TypeScript compiles (`tsc --noEmit`)
- Build succeeds (`npm run build`)

### Files

| File | Action |
|------|--------|
| `web/app/src/pages/admin/ClassificationSettingsPage.tsx` | Create |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — add AI classification card |
| `web/app/src/router.tsx` | Edit — add route |
| `web/app/src/components/layout/Sidebar.tsx` | Edit — add nav item |
| `web/app/src/types/index.ts` | Edit — add classification types |
| `web/app/src/locales/en.ts` | Edit — add ~30 keys |
| `web/app/src/locales/es.ts` | Edit — add ~30 keys |

---

## Recommended Implementation Order

1. **F0** — Classification Service (~1 session): domain types, AI adapters, prompt design, unit tests
2. **F1** — Company Configuration (~1 session): migration, entity, CRUD, API endpoints, tests
3. **F2** — Request Integration (~1-2 sessions): service, scoring extension, override logic, tests
4. **F3** — Frontend UX (~1 session): settings page, classification card, i18n

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1 → F2 → F3)
- [x] Each feature independently testable
- [x] Vertical slices — F0 delivers a reusable service, F1 delivers admin CRUD, F2 delivers the core behavior, F3 delivers visibility
- [x] Backward compatible — requests without AI classification continue to work
- [x] No overlapping scope between features
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (service + config + integration + frontend)

## Risk Notes

- **Latency:** AI classification adds ~1-3 seconds to request creation. The timeout (default 10s) ensures the worst case is bounded.
- **Cost:** Each request creation triggers an LLM call. The per-company enable/disable toggle mitigates this.
- **Prompt injection:** Employee request descriptions are user-controlled input sent to an LLM. The prompt design must clearly separate system instructions from user content.
- **Model accuracy:** Classification quality depends on the chosen model. Companies can experiment with different models via the config.
- **Override trust:** Overriding the user's classification may confuse employees. The "AI Classified" badge and original classification display address this.
