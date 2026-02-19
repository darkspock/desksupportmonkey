# Design: F0 — Classification Service

**Requirement:** [../../requirements.md](../../requirements.md)
**Feature:** F0 — Classification Service
**Date:** 2026-02-18

---

## Architecture Overview

```
NEW FILES:
src/request_bc/request/
├── application/
│   ├── ports.py                          # EDIT — add RequestClassifierPort
│   └── services/
│       └── request_classifier.py         # ClassificationResult, ClassificationOrchestrator
└── infrastructure/
    └── ai/
        ├── __init__.py
        ├── openai_classifier.py          # OpenAIRequestClassifier
        └── groq_classifier.py            # GroqRequestClassifier

tests/unit/request_bc/request/
├── application/services/
│   └── test_request_classifier.py
└── infrastructure/ai/
    └── test_adapters.py
```

---

## Domain Layer

### RequestClassifierPort (in `ports.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional

class RequestClassifierPort(ABC):
    @abstractmethod
    def classify(
        self,
        title: str,
        description: str,
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> Optional["ClassificationResult"]:
        """Classify a request. Returns None on any failure."""
```

### ClassificationResult (value object)

```python
@dataclass(frozen=True)
class ClassificationResult:
    type: str
    subtype: Optional[str]
    priority_hint: int       # -1 to +2
    confidence: float        # 0.0 to 1.0
```

### ClassificationOrchestrator (domain service)

```python
class ClassificationOrchestrator:
    def __init__(self, classifier: RequestClassifierPort):
        self.classifier = classifier

    def classify(
        self,
        title: str,
        description: str,
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> Optional[ClassificationResult]:
        """
        Calls the classifier and validates the result.
        Returns None if:
        - Classifier raises any exception
        - Returned type is not in valid_types
        - Returned subtype is not valid for the type
        - Type has empty subtypes list but AI suggested a subtype
        """
```

**Validation rules:**
- `result.type` must be a key in `valid_types`
- If `valid_types[result.type]` is empty (e.g., `incident: []`), `result.subtype` must be `None`
- If `valid_types[result.type]` is non-empty and `result.subtype` is not `None`, it must be in the list
- On any exception: log warning, return `None`

---

## Infrastructure Layer

### OpenAIRequestClassifier

```python
class OpenAIRequestClassifier(RequestClassifierPort):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout_seconds: int = 10):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def classify(self, title, description, valid_types, custom_instructions=None) -> Optional[ClassificationResult]:
        if not self.api_key:
            return None
        # import openai (deferred)
        # client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout_seconds)
        # response = client.chat.completions.create(
        #     model=self.model, temperature=0, max_tokens=200,
        #     response_format={"type": "json_object"},
        #     messages=[system_message, user_message]
        # )
        # Parse JSON, construct ClassificationResult
        # On any exception: log warning, return None
```

### GroqRequestClassifier

Same as OpenAI but with:
- `base_url="https://api.groq.com/openai/v1"`
- Default model: `"llama-3.1-8b-instant"`

### Prompt Design

**System message structure:**
1. Role: "You are a request classifier for an IT service desk."
2. Valid types/subtypes: JSON schema (passed dynamically, includes empty lists for types without subtypes)
3. Output format: `{"type": "...", "subtype": "..." or null, "priority_hint": N, "confidence": 0.XX}`
4. Priority hint guide: -1 = lower, 0 = normal, +1 = somewhat urgent, +2 = critical/emergency
5. Company custom instructions (if provided, clearly labeled)

**User message:** `"Title: {title}\nDescription: {description}"`

**Prompt injection defense:** User content in user message only, never in system message.

---

## Testing Strategy

### Unit — Orchestrator (~7 tests)
- Successful classification returns result
- Invalid type → returns None
- Invalid subtype for type → returns None
- Subtype for empty-subtypes type → returns None
- Classifier exception → returns None (graceful fallback)
- Confidence and priority_hint values passed through

### Unit — Adapters (~8 tests)
- OpenAI: no API key → None
- OpenAI: successful response → parsed ClassificationResult
- OpenAI: malformed JSON → None
- OpenAI: API error → None
- Groq: same 4 tests
- Mock `openai.OpenAI` client via `unittest.mock.patch`

---

## Design Decisions

1. **Port in `application/ports.py`**, adapters in `infrastructure/ai/` — correct DDD layering (adapters are infrastructure, not application).
2. **ClassificationResult is a frozen dataclass** — immutable value object, not an entity.
3. **Orchestrator is a domain service** — encapsulates validation logic without infrastructure coupling.
4. **Timeout passed to SDK client** — uses `openai.OpenAI(timeout=N)` rather than signal-based timeout.
5. **Deferred import of `openai`** — imported inside method body to avoid import errors when openai package is not installed.
