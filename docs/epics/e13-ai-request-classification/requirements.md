# Requirements: E13 - AI Request Classification

**Epic:** E13
**Date:** 2026-02-18
**Priority:** Medium
**Status:** Pending
**Depends on:** E0 (Foundation), E3 (Service Requests), E11 (Department Equipment Profiles — AI adapter pattern), E12 (Request Typification — types, subtypes, priority scoring)

---

## Problem Statement

After E12, requests have structured categories (6 types, 16 subtypes) and rule-based priority scoring. However, employees must still choose the correct type and subtype manually. This creates three problems:

1. **Misclassification** — Employees often pick the wrong category. A "my email doesn't work" request filed as `incident/other` should be `configuration/account_setup`. Technicians waste time reclassifying before they can act.
2. **Missing subtypes** — Subtype is optional, and many employees skip it. Without a subtype, the priority scorer assigns a lower score (subtype weight = 0), and technicians lose routing signal.
3. **Inconsistent priority** — The rule-based scorer in E12 is deterministic but blind to request content. A request titled "production server down, 500 users affected" and one titled "my keyboard LED color changed" both get the same incident priority if they share the same type+subtype+dept+role.

---

## Goals

1. **Classify requests automatically** using an LLM that reads the request title and description to infer the most accurate type, subtype, and a priority hint.
2. **Override when AI is more accurate** — If the AI's confidence exceeds a configurable threshold and its suggestion differs from the user's choice, use the AI classification. Store both the original user selection and the AI override for auditability.
3. **Enhance priority scoring** — Add an AI-derived content weight to the existing `PriorityScorer` so that request content (severity language, scope indicators, urgency cues) influences the final priority.
4. **Per-company configuration** — Each company can enable/disable classification, choose an AI provider (OpenAI or Groq), customize the prompt, set the confidence threshold, and select the model.
5. **Graceful degradation** — If no AI config exists, no API key is set, or the AI call fails, the system falls back to the user's original classification with no error visible to the user.

---

## Validation Decisions (Closed)

1. **Classification target:** The AI returns a structured JSON with `type`, `subtype`, `priority_hint` (-1 to +2), and `confidence` (0.0–1.0). The `priority_hint` is an additional weight fed into the existing `PriorityScorer` — it does NOT replace the scorer.
2. **Override policy:** If AI confidence >= threshold AND the AI type/subtype differs from the user's, the AI values replace the user's. The user's original values are preserved in `request.data.ai_classification.user_original`.
3. **Confidence threshold:** Configurable per company (default: 0.7, range 0.5–1.0). Below threshold, the user's classification is kept.
4. **Prompt design:** The system provides a structured prompt that lists all valid types and subtypes, plus the request title and description. The company can customize an additional instruction section of the prompt, but the structural scaffolding (valid types, JSON schema) is system-controlled.
5. **AI call timing:** Classification runs synchronously during request creation (before priority scoring). The AI call must complete within 10 seconds (configurable timeout). On timeout, fall back to user classification.
6. **Configuration scope:** Per-company, stored in a new `company_request_classification_configs` table. Follows the same pattern as `company_assignment_ai_configs` from E11.
7. **Provider support:** OpenAI and Groq, same adapters as E11 with a new port interface for classification (different from tiebreaking).
8. **Auditability:** All classification metadata is stored in `request.data.ai_classification`, including: model used, provider, confidence, AI suggestion, user original, whether override occurred, and latency.

---

## Non-Goals (This Epic)

- Real-time reclassification after creation (classification happens once at creation).
- Employee-facing "AI suggests..." UI before submission (no preview — classification is post-submit).
- Custom per-company types or subtypes (E30 — Custom Fields).
- AI-generated response suggestions or auto-replies to employees.
- Training or fine-tuning models on company-specific data.
- Budget or cost tracking for AI API calls.

---

## User Stories

### US-E13-001: AI classifies requests at creation
**As a** technician,
**I want** the system to automatically classify incoming requests using AI,
**So that** I receive correctly categorized requests without manual reclassification.

**Acceptance Criteria:**
- [ ] When a request is created and the company has AI classification enabled, the system calls an LLM with the request title and description.
- [ ] The LLM returns a structured classification: `type`, `subtype` (nullable), `priority_hint` (integer -1 to +2), and `confidence` (float 0.0–1.0).
- [ ] If confidence >= the company's configured threshold and the AI type/subtype differs, the request is saved with the AI classification.
- [ ] The user's original classification is preserved in `request.data.ai_classification.user_original`.
- [ ] The `priority_hint` from AI is passed to `PriorityScorer` as an additional weight.
- [ ] Classification metadata (confidence, model, provider, latency, override flag) is stored in `request.data.ai_classification`.
- [ ] If AI classification fails (timeout, error, no config), the request is created normally with user's classification.
- [ ] Classification adds no more than 10 seconds to request creation time (configurable timeout).

### US-E13-002: Company configures AI classification
**As an** admin,
**I want to** configure AI classification settings for my company,
**So that** I can choose the AI provider, model, and sensitivity threshold.

**Acceptance Criteria:**
- [ ] Admin can enable/disable AI classification for the company.
- [ ] Admin can select AI provider: OpenAI or Groq.
- [ ] Admin can select or enter a model name (optional — uses provider default if not set).
- [ ] Admin can set a confidence threshold (0.5–1.0, default 0.7).
- [ ] Admin can customize the additional instruction section of the classification prompt.
- [ ] Settings are saved via `PUT /api/v1/settings/request-classification`.
- [ ] Settings are retrieved via `GET /api/v1/settings/request-classification`.
- [ ] Only admin role can access these endpoints.

### US-E13-003: Classification results are visible on request detail
**As a** technician,
**I want to** see the AI classification results on the request detail page,
**So that** I can understand why a request was classified the way it was.

**Acceptance Criteria:**
- [ ] Request detail page shows an "AI Classification" card when `request.data.ai_classification` exists.
- [ ] Card displays: AI-suggested type and subtype, confidence percentage, whether the user's classification was overridden, and the original user classification (if overridden).
- [ ] Card shows the priority hint and its effect on the final priority.
- [ ] Card is only visible to technician+ roles (not to employees).
- [ ] Badge indicates "AI Classified" vs "Manual" on the request detail header.

### US-E13-004: AI enhances priority scoring
**As a** technician,
**I want** AI to detect urgency cues in request descriptions,
**So that** critical requests like "server down affecting 500 users" get higher priority than "keyboard LED color preference."

**Acceptance Criteria:**
- [ ] The AI returns a `priority_hint` weight (-1 to +2) based on content analysis.
- [ ] The `priority_hint` is added as a fifth dimension in `PriorityScorer.compute()`.
- [ ] Priority scoring breakdown (`request.data.priority_scoring`) includes the new `ai_hint_weight` field.
- [ ] When AI is not used, `ai_hint_weight` defaults to 0 (no change to existing scoring).
- [ ] Frontend priority scoring card on request detail shows the AI hint weight.

---

## Domain & Data (High-Level)

### New Entity
- `CompanyClassificationConfig`: `id`, `company_id` (unique), `is_enabled` (bool, default false), `provider` (string: openai/groq), `model` (optional string), `confidence_threshold` (float, default 0.7), `prompt_template` (optional text), `timeout_seconds` (int, default 10), timestamps.

### New Table
- `company_classification_configs`: Same pattern as `company_assignment_ai_configs`.

### Request Data Extension
- `request.data.ai_classification`:
```json
{
  "ai_used": true,
  "provider": "openai",
  "model": "gpt-4o-mini",
  "confidence": 0.85,
  "suggested_type": "configuration",
  "suggested_subtype": "account_setup",
  "priority_hint": 1,
  "override_applied": true,
  "user_original": {
    "type": "incident",
    "subtype": null
  },
  "latency_ms": 1230
}
```

### Priority Scoring Extension
- `PriorityScorer.compute()` gains a new `ai_priority_hint: int = 0` parameter.
- Scoring breakdown adds `ai_hint_weight` field.
- Score formula: `type_w + subtype_w + dept_w + role_w + ai_hint_w`.

### New Port Interface
```python
class RequestClassifierPort(ABC):
    @abstractmethod
    def classify(self, title: str, description: str, valid_types: dict) -> ClassificationResult:
        """Classify a request, returning type/subtype/priority_hint/confidence."""
```

### Classification Flow
```
Employee submits request (type, subtype?, title, description)
       │
       ▼
  Company has AI classification enabled?
       │ No ──────────────────────────┐
       │ Yes                          │
       ▼                              │
  Call LLM with title + description   │
       │                              │
       ▼                              │
  confidence >= threshold?            │
       │ No ──────────────────────────┤
       │ Yes                          │
       ▼                              │
  Override type/subtype               │
  Store user_original                 │
       │                              │
       ├──────────────────────────────┘
       ▼
  PriorityScorer.compute(
    ..., ai_priority_hint=priority_hint
  )
       │
       ▼
  Create request with final classification + scoring
```

---

## Technical Constraints

- **Reuse E11 AI adapter pattern:** OpenAI and Groq adapters with abstract port, same dependency injection style.
- **Synchronous classification:** Runs in the request creation handler (synchronous, with timeout). No Celery task needed — classification must be done before the request is saved.
- **Prompt injection defense:** The company-customizable prompt section is injected as a "system instruction" separate from user content. The user's title and description are placed in a clearly delimited user-content block.
- **Token limits:** The prompt plus title+description should not exceed 2000 tokens. Truncate description if necessary.
- **JSON mode:** Use the provider's JSON mode (OpenAI `response_format: json_object`, Groq structured output) to ensure structured responses.
- **Multi-tenant:** All config and classification data is scoped by `company_id`.
- **Backward compatibility:** Requests created without AI classification continue to work. The `ai_classification` key in `request.data` is optional.
- **Environment variables:** Reuse existing `OPENAI_API_KEY` and `GROQ_API_KEY` from `core/config.py` `AISettings`.

---

## Definition of Done

- [ ] Classification service with OpenAI and Groq adapters, structured JSON output.
- [ ] Per-company configuration (CRUD) with enabled/disabled toggle, provider, model, threshold, prompt.
- [ ] Integration into request creation: classify → override if confident → score with AI hint.
- [ ] Classification metadata stored on request for auditability.
- [ ] Priority scorer extended with `ai_priority_hint` weight.
- [ ] Admin settings page for AI classification configuration.
- [ ] Request detail page shows AI classification card (technician+).
- [ ] Priority scoring card updated with AI hint weight.
- [ ] Graceful fallback when AI is unavailable (no error, no degradation).
- [ ] Unit tests: classification service, override logic, scoring extension, config CRUD.
- [ ] Integration tests: create request with/without AI, config endpoints.
- [ ] i18n keys for all new UI text (English + Spanish).
