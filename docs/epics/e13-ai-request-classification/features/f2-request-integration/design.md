# Design: F2 — Request Integration

**Requirement:** [../../requirements.md](../../requirements.md)
**Feature:** F2 — Request Integration
**Date:** 2026-02-18

---

## Architecture Overview

```
NEW FILES:
src/request_bc/request/application/services/
└── classification_service.py        # ClassificationService, ClassificationServiceResult

tests/unit/request_bc/request/application/services/
└── test_classification_service.py

MODIFIED FILES:
src/request_bc/request/application/services/priority_scorer.py    # Add ai_priority_hint
src/request_bc/request/application/commands/create_request.py     # Add ai_priority_hint, ai_classification
adapters/http/api/requests/routers.py                             # Call ClassificationService
adapters/http/api/requests/dependencies.py                        # Add classification config repo
```

---

## Application Layer

### ClassificationService (application service)

Business logic for classifying requests lives here — NOT in the router, NOT in the command handler.

```python
@dataclass(frozen=True)
class ClassificationServiceResult:
    resolved_type: str
    resolved_subtype: Optional[str]
    ai_priority_hint: int
    ai_classification: Optional[dict]

class ClassificationService:
    def __init__(
        self,
        classifier: RequestClassifierPort,
        config: CompanyClassificationConfig,
        valid_types: dict[str, list[str]],
    ): ...

    def classify_request(
        self,
        title: str,
        description: str,
        user_type: str,
        user_subtype: Optional[str],
    ) -> ClassificationServiceResult:
        """
        1. Call ClassificationOrchestrator.classify()
        2. Measure latency (time.time() before/after)
        3. Build ai_classification metadata dict
        4. If result and confidence >= threshold and type/subtype differs:
           a. Pre-validate AI type against RequestType enum
           b. Pre-validate AI subtype against VALID_SUBTYPES[type]
           c. If valid: override, store user_original
           d. If invalid: skip override
        5. Return ClassificationServiceResult with resolved values
        """

    @staticmethod
    def build_classifier(
        config: CompanyClassificationConfig,
        ai_settings,  # core.config.AISettings
    ) -> Optional[RequestClassifierPort]:
        """
        Factory: build the correct adapter based on config.provider.
        - AIProvider.OPENAI → OpenAIRequestClassifier(api_key, model, timeout)
        - AIProvider.GROQ → GroqRequestClassifier(api_key, model, timeout)
        Returns None if no API key available.
        """
```

**AI classification metadata dict structure** (stored in `request.data.ai_classification`):
```python
{
    "ai_used": True,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "confidence": 0.85,
    "suggested_type": "configuration",
    "suggested_subtype": "account_setup",
    "priority_hint": 1,
    "override_applied": True,
    "user_original": {"type": "incident", "subtype": None},
    "latency_ms": 1230,
}
```

When AI fails or is unavailable: `{"ai_used": False}`

### PriorityScorer Extension

```python
class PriorityScorer:
    def compute(
        self,
        request_type: RequestType,
        subtype: Optional[str],
        department_priority_weight: int,
        user_role: str,
        ai_priority_hint: int = 0,    # NEW — defaulted, backward compatible
    ) -> tuple[RequestPriority, dict]:
        # ...
        ai_hint_w = ai_priority_hint
        raw_score = type_w + subtype_w + dept_w + role_w + ai_hint_w
        breakdown = {
            "type_weight": type_w,
            "subtype_weight": subtype_w,
            "department_weight": dept_w,
            "role_weight": role_w,
            "ai_hint_weight": ai_hint_w,    # NEW
            "raw_score": raw_score,
        }
```

### CreateRequestCommand Extension

```python
@dataclass
class CreateRequestCommand(Command):
    # ... existing fields ...
    ai_priority_hint: int = 0                  # NEW — resolved by ClassificationService
    ai_classification: Optional[dict] = None   # NEW — metadata from ClassificationService

class CreateRequestCommandHandler(CommandHandler[CreateRequestCommand]):
    def handle(self, command):
        # ... existing flow ...
        priority, breakdown = PriorityScorer().compute(
            ..., ai_priority_hint=command.ai_priority_hint    # NEW
        )
        # ... create request ...
        # Merge ai_classification into request.data
        if command.ai_classification:
            data = request.data or {}
            data["ai_classification"] = command.ai_classification
            request.data = data
```

---

## HTTP Layer

### Router Changes

```python
@router.post("/")
def create_request(
    body: CreateRequestSchema,
    current_user = Depends(get_current_user),
    request_repo = Depends(get_request_repo),
    classification_config_repo = Depends(get_classification_config_repo),  # NEW
):
    # 1. Look up classification config
    config = classification_config_repo.find_by_company(current_user.company_id)

    # 2. Run classification if enabled
    ai_priority_hint = 0
    ai_classification = None
    resolved_type = body.type
    resolved_subtype = body.subtype

    if config and config.is_enabled:
        classifier = ClassificationService.build_classifier(config, settings.ai)
        if classifier:
            valid_types = {t.value: [s.value for s in subs] for t, subs in VALID_SUBTYPES.items()}
            service = ClassificationService(classifier, config, valid_types)
            result = service.classify_request(body.title, body.description, body.type, body.subtype)
            ai_priority_hint = result.ai_priority_hint
            ai_classification = result.ai_classification
            resolved_type = result.resolved_type
            resolved_subtype = result.resolved_subtype

    # 3. Build command with resolved values
    command = CreateRequestCommand(
        type=resolved_type,
        subtype=resolved_subtype,
        ai_priority_hint=ai_priority_hint,
        ai_classification=ai_classification,
        ...
    )
```

### Dependencies

```python
# In adapters/http/api/requests/dependencies.py
def get_classification_config_repo(db: Session = Depends(get_db)) -> ClassificationConfigRepository:
    return ClassificationConfigRepository(db)
```

---

## Testing Strategy

### Unit — ClassificationService (~9 tests)
- AI confident + type differs → override applied, user_original stored
- AI confident + same type → no override, ai_used=True
- AI below threshold → no override
- AI returns None (failure) → fallback, ai_used=False
- AI suggests invalid type → pre-validation catches, no override
- AI suggests invalid subtype → pre-validation catches, no override
- Latency recorded in metadata
- build_classifier returns OpenAI adapter for openai provider
- build_classifier returns Groq adapter for groq provider

### Unit — PriorityScorer (~4 tests)
- ai_priority_hint=0 → ai_hint_weight=0
- ai_priority_hint=2 → raw_score +2
- ai_priority_hint=-1 → raw_score -1
- ai_priority_hint pushes medium → urgent

### Unit — CreateRequestCommand (~4 tests)
- ai_priority_hint passed to scorer
- ai_priority_hint=0 default → scorer unaffected
- ai_classification merged into request.data
- ai_classification=None → no key in data

### Integration (~3 tests)
- Create request with AI enabled (mock adapter) → metadata in response
- Create request without config → normal, no ai_classification
- Create request with AI override → type/subtype overridden

---

## Design Decisions

1. **Classification logic in `ClassificationService`** (application service) — business logic belongs in the domain/application layer, not in routers. The router only wires dependencies and calls the service.
2. **`ClassificationServiceResult` carries resolved values** — the router doesn't need to understand override logic. It just passes `result.resolved_type` etc. to the command.
3. **`CreateRequestCommand` receives only resolved values** (`ai_priority_hint`, `ai_classification`) — no raw config, no API keys, no infrastructure concerns in the command.
4. **`build_classifier` is a static factory method** on `ClassificationService` — centralizes adapter construction logic in the service, not scattered in the router.
5. **Pre-validation against `VALID_SUBTYPES`** before override — prevents domain entity validation failures that would surface as 422 errors instead of graceful fallback.
6. **Latency measurement in `ClassificationService`** — `time.time()` before and after the classify call, converted to `latency_ms`.
