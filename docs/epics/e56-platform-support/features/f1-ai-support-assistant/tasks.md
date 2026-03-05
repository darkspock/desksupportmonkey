# Implementation Tasks: F1 — AI Support Assistant

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 16
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Exceptions | 1 | S |
| Domain — Interface | 1 | S |
| Infrastructure — Providers | 1 | M |
| Infrastructure — System Prompt | 1 | S |
| Application — Command | 1 | M |
| Configuration | 1 | S |
| HTTP — Schemas + Router | 1 | M |
| HTTP — Register Router | 1 | S |
| Tests — Unit | 1 | M |
| Tests — Integration | 1 | M |
| Frontend — Hook | 1 | S |
| Frontend — Components | 1 | M |
| Frontend — i18n | 1 | S |
| Frontend — Mount Widget | 1 | S |
| Collateral — HelpPanel | 1 | S |
| Collateral — .env.example | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create domain exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create the three domain exceptions for the AI assistant feature. Also create the `support_bc` package structure with `__init__.py` files.

**Files:**
- `src/support_bc/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/domain/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/domain/exceptions.py` (new)

**Implementation:**
```python
# src/support_bc/ai_assistant/domain/exceptions.py
class AIProviderError(Exception):
    """A single AI provider call failed."""
    pass

class AIRateLimitExceededError(Exception):
    """User exceeded the AI query rate limit."""
    pass

class AIUnavailableError(Exception):
    """All AI providers failed."""
    pass
```

**Acceptance Criteria:**
- [x] `AIProviderError`, `AIRateLimitExceededError`, `AIUnavailableError` defined
- [x] `support_bc` package structure created with all `__init__.py` files

---

### TASK-002: Create SupportAIProviderInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the ABC interface (port) for AI chat providers.

**File:** `src/support_bc/ai_assistant/domain/service.py`

**Implementation:**
```python
from abc import ABC, abstractmethod

class SupportAIProviderInterface(ABC):
    """Port for AI chat providers."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], system_prompt: str) -> str:
        """Send messages to AI and return response text.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: System instructions for the AI

        Returns:
            AI response text

        Raises:
            AIProviderError: If the provider call fails
        """
        ...
```

**Acceptance Criteria:**
- [x] ABC with single `chat()` method
- [x] Accepts `messages: list[dict[str, str]]` and `system_prompt: str`
- [x] Returns `str`
- [x] Docstring documents `AIProviderError` raise

---

## Phase 2: Infrastructure Layer

### TASK-003: Create AnthropicProvider, GroqProvider, and provider factory

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002

**Description:**
Create both AI provider implementations and the factory functions that select the primary/fallback provider based on config.

**Files:**
- `src/support_bc/ai_assistant/infrastructure/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/infrastructure/anthropic_provider.py` (new)
- `src/support_bc/ai_assistant/infrastructure/groq_provider.py` (new)
- `src/support_bc/ai_assistant/infrastructure/provider_factory.py` (new)

**Implementation — AnthropicProvider:**
```python
import logging
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface
from src.support_bc.ai_assistant.domain.exceptions import AIProviderError

logger = logging.getLogger(__name__)

class AnthropicProvider(SupportAIProviderInterface):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict[str, str]], system_prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.warning("Anthropic provider failed: %s", e)
            raise AIProviderError(str(e)) from e
```

**Implementation — GroqProvider:**
```python
import logging
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface
from src.support_bc.ai_assistant.domain.exceptions import AIProviderError

logger = logging.getLogger(__name__)

class GroqProvider(SupportAIProviderInterface):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict[str, str]], system_prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            all_messages = [{"role": "system", "content": system_prompt}] + messages
            response = client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                max_tokens=1024,
                temperature=0.7,
            )
            content = response.choices[0].message.content
            return content if isinstance(content, str) else ""
        except Exception as e:
            logger.warning("Groq provider failed: %s", e)
            raise AIProviderError(str(e)) from e
```

**Implementation — provider_factory:**
```python
from core.config import settings
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface
from src.support_bc.ai_assistant.infrastructure.anthropic_provider import AnthropicProvider
from src.support_bc.ai_assistant.infrastructure.groq_provider import GroqProvider

def get_ai_provider() -> SupportAIProviderInterface:
    """Return primary provider based on config."""
    provider = settings.ai.AI_SUPPORT_PROVIDER
    if provider == "anthropic":
        return AnthropicProvider(
            api_key=settings.ai.ANTHROPIC_API_KEY,
            model=settings.ai.AI_SUPPORT_MODEL or "claude-haiku-4-5-20251001",
        )
    return GroqProvider(
        api_key=settings.ai.GROQ_API_KEY,
        model=settings.ai.AI_SUPPORT_MODEL or "llama-3.3-70b-versatile",
    )

def get_fallback_provider() -> SupportAIProviderInterface:
    """Return the other provider for failover."""
    provider = settings.ai.AI_SUPPORT_PROVIDER
    if provider == "anthropic":
        return GroqProvider(
            api_key=settings.ai.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
        )
    return AnthropicProvider(
        api_key=settings.ai.ANTHROPIC_API_KEY,
        model="claude-haiku-4-5-20251001",
    )
```

**Acceptance Criteria:**
- [x] `AnthropicProvider` implements `SupportAIProviderInterface`, uses `anthropic` SDK, wraps all errors in `AIProviderError`
- [x] `GroqProvider` implements `SupportAIProviderInterface`, uses `openai` SDK with Groq base URL, wraps all errors in `AIProviderError`
- [x] `get_ai_provider()` returns correct provider based on `AI_SUPPORT_PROVIDER` config (default: groq)
- [x] `get_fallback_provider()` returns the OTHER provider for failover

---

### TASK-004: Create system prompt builder

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Create the `build_system_prompt` function that extracts `help.*` keys from the en.ts locale file and combines them with company context.

**File:** `src/support_bc/ai_assistant/infrastructure/system_prompt.py`

**Implementation:**
```python
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_help_content: dict[str, str] | None = None

def _load_help_content() -> dict[str, str]:
    """Extract help.* keys from en.ts locale file."""
    global _help_content
    if _help_content is not None:
        return _help_content

    _help_content = {}
    locale_path = Path(__file__).resolve().parents[4] / "web" / "app" / "src" / "locales" / "en.ts"
    try:
        text = locale_path.read_text(encoding="utf-8")
        for match in re.finditer(r"'(help\.\w+)':\s*'([^']*(?:\\'[^']*)*)'", text):
            key = match.group(1)
            value = match.group(2).replace("\\'", "'")
            _help_content[key] = value
    except Exception as e:
        logger.warning("Could not load help content: %s", e)
    return _help_content


def build_system_prompt(
    company_name: str,
    plan_tier: str,
    enabled_modules: list[str],
) -> str:
    """Build the AI assistant system prompt with help content and company context."""
    help_content = _load_help_content()

    help_text = "\n".join(
        f"- {key.replace('help.', '')}: {value}"
        for key, value in sorted(help_content.items())
    )

    modules_text = ", ".join(enabled_modules) if enabled_modules else "all modules"

    return f"""You are the DSM Control support assistant — a helpful, concise AI that answers questions about the DSM Control IT Service Desk & Asset Inventory platform.

## Company Context
- Company: {company_name}
- Plan: {plan_tier}
- Enabled modules: {modules_text}

## Your Knowledge Base
{help_text}

## Rules
- Answer questions about DSM Control features, workflows, and configuration
- Be concise and helpful — aim for 2-4 sentences unless the user asks for detail
- If the user's plan doesn't include a feature, mention they may need to upgrade
- If you're unsure or the question is about a bug, billing, or account issue, suggest creating a support ticket
- Never make up features that don't exist in DSM Control
- Respond in the same language the user writes in
- Do not answer questions unrelated to DSM Control"""
```

**Acceptance Criteria:**
- [x] `_load_help_content()` extracts all `help.*` keys from `en.ts` (approx. 75 keys)
- [x] Results are cached (loaded once, reused)
- [x] `build_system_prompt()` includes company name, plan tier, and enabled modules
- [x] System prompt includes rules about response style and scope

---

## Phase 3: Application Layer

### TASK-005: Create AIChatCommand + AIChatCommandHandler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-002, TASK-003, TASK-004

**Description:**
Create the command and handler that process AI chat messages with rate limiting (Redis) and provider failover.

**Files:**
- `src/support_bc/ai_assistant/application/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/application/commands/__init__.py` (new — empty)
- `src/support_bc/ai_assistant/application/commands/ai_chat.py` (new)

**Implementation:**
```python
import logging
from dataclasses import dataclass, field

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ai_assistant.domain.exceptions import (
    AIProviderError,
    AIRateLimitExceededError,
    AIUnavailableError,
)
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface

logger = logging.getLogger(__name__)


@dataclass
class AIChatCommand(Command):
    user_id: str
    company_id: str
    company_name: str
    plan_tier: str
    enabled_modules: list[str]
    messages: list[dict[str, str]]


class AIChatCommandHandler(CommandHandler[AIChatCommand]):
    """Handle AI chat with rate limiting and provider failover.

    Note: This handler stores the AI response in `self.response` after execution.
    The router reads this value after calling handle().
    """

    MAX_QUERIES_PER_HOUR = 20

    def __init__(
        self,
        primary_provider: SupportAIProviderInterface,
        fallback_provider: SupportAIProviderInterface,
        redis_client,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.redis = redis_client
        self.response: str = ""

    def handle(self, command: AIChatCommand) -> None:
        # 1. Check rate limit
        rate_key = f"ai_chat_rate:{command.user_id}"
        current = self.redis.get(rate_key)
        if current is not None and int(current) >= self.MAX_QUERIES_PER_HOUR:
            raise AIRateLimitExceededError("Rate limit exceeded: max 20 queries per hour")

        # 2. Build system prompt
        from src.support_bc.ai_assistant.infrastructure.system_prompt import build_system_prompt
        system_prompt = build_system_prompt(
            company_name=command.company_name,
            plan_tier=command.plan_tier,
            enabled_modules=command.enabled_modules,
        )

        # 3. Try primary provider
        try:
            self.response = self.primary_provider.chat(command.messages, system_prompt)
        except AIProviderError:
            # 4. Failover to secondary
            logger.info("Primary AI provider failed, trying fallback")
            try:
                self.response = self.fallback_provider.chat(command.messages, system_prompt)
            except AIProviderError:
                raise AIUnavailableError(
                    "AI assistant is temporarily unavailable. Please try again later or create a support ticket."
                )

        # 5. Increment rate limit counter
        pipe = self.redis.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, 3600)
        pipe.execute()
```

**Acceptance Criteria:**
- [x] `AIChatCommand` inherits from `Command` with all fields from design
- [x] `AIChatCommandHandler` inherits from `CommandHandler[AIChatCommand]`
- [x] Rate limiting: checks Redis counter, raises `AIRateLimitExceededError` when >= 20
- [x] Failover: primary fails → try fallback → if both fail, raise `AIUnavailableError`
- [x] Response stored in `self.response` (result container pattern)
- [x] Redis counter incremented ONLY on success (after provider call)
- [x] Counter uses 3600s TTL (1 hour)

---

## Phase 4: Configuration

### TASK-006: Add AI config fields and anthropic dependency

**Phase:** Configuration
**Complexity:** S
**Dependencies:** None

**Description:**
Add new config fields to `AISettings` and add the `anthropic` Python package to `pyproject.toml`.

**Files to modify:**
- `core/config.py` → `AISettings` class
- `pyproject.toml` → dependencies

**Changes — core/config.py:**
Add to `AISettings`:
```python
class AISettings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""           # NEW
    AI_SUPPORT_PROVIDER: str = "groq"     # NEW — "anthropic" or "groq"
    AI_SUPPORT_MODEL: str = ""            # NEW — override default model

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

**Changes — pyproject.toml:**
Add `anthropic` to dependencies.

**Acceptance Criteria:**
- [x] `ANTHROPIC_API_KEY`, `AI_SUPPORT_PROVIDER`, `AI_SUPPORT_MODEL` added to `AISettings`
- [x] Defaults: `ANTHROPIC_API_KEY=""`, `AI_SUPPORT_PROVIDER="groq"`, `AI_SUPPORT_MODEL=""`
- [x] `anthropic` package added to `pyproject.toml` dependencies

---

## Phase 5: HTTP Layer

### TASK-007: Create AI support schemas, company context dependency, and router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-005, TASK-006

**Description:**
Create the Pydantic schemas, the company context dependency, and the router for `POST /api/v1/my/ai-support`.

**Files:**
- `adapters/http/api/my/schemas.py` (modify — add schemas)
- `adapters/http/api/my/ai_support_router.py` (new)

**Implementation — schemas additions:**
```python
class AIChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)

class AIChatRequest(BaseModel):
    messages: list[AIChatMessage] = Field(..., min_length=1, max_length=50)
```

**Implementation — router:**
```python
import redis
from dataclasses import dataclass
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.my.schemas import AIChatRequest
from core.config import settings
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.company_bc.nav_config.infrastructure.repository import NavConfigRepository
from src.support_bc.ai_assistant.application.commands.ai_chat import (
    AIChatCommand,
    AIChatCommandHandler,
)
from src.support_bc.ai_assistant.domain.exceptions import (
    AIRateLimitExceededError,
    AIUnavailableError,
)
from src.support_bc.ai_assistant.infrastructure.provider_factory import (
    get_ai_provider,
    get_fallback_provider,
)

router = APIRouter(prefix="/api/v1/my", tags=["ai-support"])


@dataclass
class CompanyContext:
    name: str
    plan_tier: str
    enabled_modules: list[str]


def get_company_context(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
) -> CompanyContext:
    company = CompanyRepository(db).find_by_id(current_user.company_id)
    nav_config = NavConfigRepository(db).find_by_company(current_user.company_id)
    return CompanyContext(
        name=company.name if company else "",
        plan_tier=company.plan.value if company else "free",
        enabled_modules=nav_config.enabled_modules if nav_config else [],
    )


def _get_redis():
    return redis.Redis.from_url(settings.celery.CELERY_BROKER_URL, decode_responses=True)


@router.post("/ai-support", status_code=status.HTTP_200_OK)
def ai_chat(
    body: AIChatRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    # Resolve company context
    company = CompanyRepository(db).find_by_id(current_user.company_id)
    nav_config = NavConfigRepository(db).find_by_company(current_user.company_id)

    handler = AIChatCommandHandler(
        primary_provider=get_ai_provider(),
        fallback_provider=get_fallback_provider(),
        redis_client=_get_redis(),
    )
    try:
        handler.handle(
            AIChatCommand(
                user_id=current_user.id,
                company_id=current_user.company_id or "",
                company_name=company.name if company else "",
                plan_tier=company.plan.value if company else "free",
                enabled_modules=nav_config.enabled_modules if nav_config else [],
                messages=[{"role": m.role, "content": m.content} for m in body.messages],
            )
        )
    except AIRateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: max 20 AI queries per hour. Please try again later.",
        )
    except AIUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return {"data": {"response": handler.response}}
```

**Acceptance Criteria:**
- [x] `AIChatMessage` schema validates `role` as "user" or "assistant", `content` 1-4000 chars
- [x] `AIChatRequest` schema validates 1-50 messages
- [x] Router requires `TECHNICIAN` role (which includes ADMIN in role hierarchy)
- [x] Company context (name, plan, modules) fetched from repositories
- [x] `AIRateLimitExceededError` → 429
- [x] `AIUnavailableError` → 503
- [x] Success returns `{"data": {"response": "..."}}`

---

### TASK-008: Register AI support router in app.py

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-007

**Description:**
Import and register the new AI support router in `app.py`.

**File to modify:** `app.py`

**Changes:**
```python
from adapters.http.api.my.ai_support_router import router as ai_support_router
# ...
application.include_router(ai_support_router)
```

**Acceptance Criteria:**
- [x] Router imported and registered
- [x] `POST /api/v1/my/ai-support` endpoint accessible

---

## Phase 6: Tests

### TASK-009: Unit tests — handler, providers, system prompt, factory

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Create unit tests for the AI chat command handler (rate limiting, failover, response capture), provider implementations (mock SDK calls), system prompt builder, and provider factory.

**Files:**
- `tests/unit/support_bc/__init__.py` (new — empty)
- `tests/unit/support_bc/ai_assistant/__init__.py` (new — empty)
- `tests/unit/support_bc/ai_assistant/test_ai_chat.py` (new)
- `tests/unit/support_bc/ai_assistant/test_system_prompt.py` (new)

**Key test scenarios for `test_ai_chat.py`:**
1. **Primary success:** Mock provider returns response → `handler.response` is set
2. **Failover success:** Primary raises `AIProviderError`, fallback succeeds → response from fallback
3. **Both fail:** Both raise `AIProviderError` → `AIUnavailableError` raised
4. **Rate limit exceeded:** Redis returns count >= 20 → `AIRateLimitExceededError` raised
5. **Rate limit not exceeded:** Redis returns count < 20 → proceeds normally
6. **Redis counter incremented:** On success, verify `pipeline.incr` and `pipeline.expire` called
7. **Counter NOT incremented on failure:** If both providers fail, counter stays unchanged

**Key test scenarios for `test_system_prompt.py`:**
1. **Company context included:** Company name, plan tier, modules appear in output
2. **Empty modules:** "all modules" used when list is empty
3. **Help content loaded:** Output includes help text entries

**Acceptance Criteria:**
- [x] All 7 handler test scenarios pass
- [x] All 3 system prompt test scenarios pass
- [x] Providers and Redis are mocked (no real API calls)
- [x] `make test` passes

---

### TASK-010: Integration tests — AI support endpoint

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Create integration tests for the `POST /api/v1/my/ai-support` endpoint.

**File:** `tests/integration/test_ai_support_endpoints.py`

**Key test scenarios:**
1. **401 without auth:** No token → 401
2. **403 for EMPLOYEE role:** EMPLOYEE user → 403
3. **200 success:** ADMIN user with mocked provider → 200 with response
4. **200 for TECHNICIAN:** TECHNICIAN user → 200
5. **429 rate limit:** Mock Redis to return count >= 20 → 429
6. **503 unavailable:** Both providers mocked to fail → 503
7. **422 invalid messages:** Empty messages array → 422
8. **422 invalid role:** Message with role "system" → 422

**Acceptance Criteria:**
- [x] All 8 test scenarios pass
- [x] AI providers are mocked (no real API calls in tests)
- [x] Redis is mocked
- [x] `make test-integration` passes

---

## Phase 7: Frontend

### TASK-011: Create useAIChat hook

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-008

**Description:**
Create a React hook that manages AI chat state and API calls.

**File:** `web/app/src/hooks/useAIChat.ts`

**Implementation requirements:**
- `messages` state: array of `{role: "user" | "assistant", content: string}`
- `sendMessage(content: string)`: appends user message, calls `POST /api/v1/my/ai-support` with full history, appends AI response
- `isLoading` state: true while API call in progress
- `error` state: error message (rate limit, unavailable, etc.)
- `resetChat()`: clears all messages
- Handles 429 → set specific rate limit error message
- Handles 503 → set unavailable error message

**Acceptance Criteria:**
- [x] Hook manages messages array in React state
- [x] `sendMessage()` sends full conversation history with each request
- [x] Loading, error, and rate limit states handled
- [x] `resetChat()` clears conversation

---

### TASK-012: Create AIChatWidget and AIChatMessage components

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-011

**Description:**
Create the floating chat button and slide-in panel UI, plus the individual message bubble component.

**Files:**
- `web/app/src/components/support/AIChatWidget.tsx` (new)
- `web/app/src/components/support/AIChatMessage.tsx` (new)

**AIChatWidget requirements:**
- Floating button (bottom-right corner, offset from help button)
- Visible only for ADMIN/TECHNICIAN roles
- Click toggles slide-in panel from right edge
- Panel contains: header with title + close button, message list with auto-scroll, input field with send button
- Loading indicator (typing dots or spinner) while AI responds
- "Create support ticket" button — disabled with tooltip "Coming soon" (until F2)
- Error states: rate limit message, unavailable message
- Disclaimer text at bottom

**AIChatMessage requirements:**
- User messages: right-aligned, primary color background
- AI messages: left-aligned, secondary/muted background
- Timestamp (relative, e.g., "just now", "2m ago")
- Markdown support for AI responses (basic: bold, links, lists)

**Acceptance Criteria:**
- [x] Floating button visible for ADMIN/TECHNICIAN only
- [x] Slide-in panel opens/closes on button click
- [x] Message list with auto-scroll to latest
- [x] Input field with send on Enter and send button
- [x] Loading state shown during AI response
- [x] "Create support ticket" button rendered but disabled
- [x] Rate limit and unavailable error messages displayed
- [x] User and AI messages styled differently
- [x] Panel uses same visual language as HelpPanel (E51)

---

### TASK-013: Add i18n keys for AI chat (en.ts + es.ts)

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add all AI chat-related i18n keys in both English and Spanish locale files.

**Files to modify:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys to add:**
```
ai_chat.title: "AI Support Assistant"
ai_chat.placeholder: "Ask a question about DSM..."
ai_chat.send: "Send"
ai_chat.disclaimer: "AI responses may not always be accurate. For critical issues, create a support ticket."
ai_chat.escalate: "Create support ticket"
ai_chat.escalate_tooltip: "Coming soon"
ai_chat.rate_limit: "You've reached the query limit (20/hour). Please try again later."
ai_chat.unavailable: "AI assistant is temporarily unavailable. Please try again later or create a support ticket."
ai_chat.error: "Something went wrong. Please try again."
ai_chat.welcome: "Hi! I'm the DSM support assistant. Ask me anything about how to use DSM Control."
```

**Acceptance Criteria:**
- [x] All 10 keys added to `en.ts`
- [x] All 10 keys translated and added to `es.ts`
- [x] TypeScript compiles cleanly

---

### TASK-014: Mount AIChatWidget in app layout

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-012

**Description:**
Render the `<AIChatWidget />` component in the authenticated app layout, so it appears on all pages for ADMIN/TECHNICIAN users.

**File to modify:** `web/app/src/App.tsx` or the authenticated layout component

**Changes:**
- Import `AIChatWidget`
- Render it inside the authenticated layout (alongside the existing help button)
- The widget itself handles role-based visibility internally

**Acceptance Criteria:**
- [x] `AIChatWidget` rendered in authenticated layout
- [x] Visible on all pages when logged in as ADMIN or TECHNICIAN
- [x] Not visible for EMPLOYEE role
- [x] Does not interfere with existing HelpPanel

---

## Phase 8: Collateral Changes

### TASK-015: Add "AI Assistant" link to HelpPanel

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-012

**Description:**
Add a button/link in the existing HelpPanel (E51) footer that opens the AI chat widget. Only visible for ADMIN/TECHNICIAN.

**File to modify:** `web/app/src/components/help/HelpPanel.tsx`

**Changes:**
- Add "Ask AI Assistant" button in the help panel footer
- Clicking it closes the help panel and opens the AI chat widget
- Only visible for ADMIN/TECHNICIAN roles

**Acceptance Criteria:**
- [x] "Ask AI Assistant" button in HelpPanel footer
- [x] Clicking opens AI chat and closes help panel
- [x] Only visible for ADMIN/TECHNICIAN

---

### TASK-016: Update .env.example with AI config vars

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
Add the new AI-related environment variables to `.env.example`.

**File to modify:** `.env.example`

**Variables to add:**
```
# AI Support Assistant
ANTHROPIC_API_KEY=
AI_SUPPORT_PROVIDER=groq
AI_SUPPORT_MODEL=
```

**Acceptance Criteria:**
- [x] All 3 new env vars documented in `.env.example`
- [x] Default values match `AISettings` defaults

---

## Dependency Graph

```
TASK-001 (Exceptions)
    └── TASK-002 (Interface)
            └── TASK-003 (Providers + Factory)
                    └── TASK-005 (Command Handler) ── depends on ── TASK-004 (System Prompt)
                            └── TASK-007 (Schemas + Router)
                                    └── TASK-008 (Register Router)
                                            ├── TASK-010 (Integration Tests)
                                            └── TASK-011 (useAIChat Hook)
                                                    └── TASK-012 (Components)
                                                            ├── TASK-014 (Mount Widget)
                                                            └── TASK-015 (HelpPanel Link)

TASK-005 ── TASK-009 (Unit Tests)
TASK-006 (Config) ── independent, do early
TASK-013 (i18n) ── independent, do early
TASK-016 (.env.example) ── depends on TASK-006
```

## Execution Order

**Batch 1 (Parallel — no dependencies):**
- TASK-001: Domain exceptions
- TASK-004: System prompt builder
- TASK-006: AI config fields + anthropic dependency
- TASK-013: i18n keys

**Batch 2 (Sequential after Batch 1):**
- TASK-002: SupportAIProviderInterface (after TASK-001)
- TASK-016: .env.example (after TASK-006)

**Batch 3 (After TASK-002):**
- TASK-003: Provider implementations + factory

**Batch 4 (After TASK-003 + TASK-004):**
- TASK-005: AIChatCommand + Handler

**Batch 5 (After TASK-005 + TASK-006):**
- TASK-007: Schemas + Router
- TASK-009: Unit tests (parallel with TASK-007)

**Batch 6 (After TASK-007):**
- TASK-008: Register router in app.py

**Batch 7 (After TASK-008):**
- TASK-010: Integration tests
- TASK-011: useAIChat hook

**Batch 8 (After TASK-011 + TASK-013):**
- TASK-012: AIChatWidget + AIChatMessage components

**Batch 9 (After TASK-012):**
- TASK-014: Mount widget in layout
- TASK-015: HelpPanel link

## Final Checklist

- [x] All 16 tasks completed
- [x] All tests passing (`make test` + `make test-integration`)
- [x] mypy passes (`make lint`)
- [x] TypeScript compiles cleanly
- [x] Rate limiting works (20/hour)
- [x] Provider failover works
- [x] i18n complete (en + es)
- [x] Widget visible for ADMIN/TECHNICIAN only
