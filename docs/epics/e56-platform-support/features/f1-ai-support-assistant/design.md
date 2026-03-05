# Solution Design: F1 — AI Support Assistant

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `support_bc` (new)

## Summary

A stateless AI chat feature where the backend proxies user messages to an LLM provider (Anthropic or Groq), building a system prompt from DSM help content and company context. The frontend manages conversation history (session-scoped) and sends the full message list with each request. Rate limiting is enforced per-user in Redis. Provider failover retries with the secondary provider on failure.

No database tables are needed — the AI conversation is ephemeral (frontend state only). The backend is a single command with provider adapters.

## Architecture Decision

**Approach chosen:** Stateless proxy with provider abstraction

- **No new database entities** — AI conversations are not persisted. The frontend holds the message history and sends it with each request. This keeps the feature simple, avoids migration, and matches the epic's "session-only" decision.
- **Command (not Query)** — Although the endpoint returns data, calling an external AI API is a side effect (cost, rate limit consumption, external network call). Using a command that raises exceptions for errors is cleaner than a query. The command handler returns `None` per CQRS; the AI response is captured via a result container pattern (the handler stores the response on itself after execution, and the router reads it).
- **Alternative considered: Query** — Would work but violates the principle that queries are pure reads. AI calls have side effects (billing, rate limits).
- **Alternative considered: Application Service** — Simpler but bypasses the command bus pattern used everywhere else. We'll use a direct handler instantiation (same pattern as `create_magic_link.py`).

**Provider abstraction:** ABC interface `SupportAIProviderInterface` with `AnthropicProvider` and `GroqProvider` implementations. Factory function selects based on `AI_SUPPORT_PROVIDER` env var.

**Rate limiting:** Redis-based counter (INCR + EXPIRE) rather than DB query. This avoids creating a table just for rate tracking, and Redis is already available (Celery broker). Follows the same conceptual pattern as magic link rate limiting but uses Redis for ephemeral counts.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| AI adapter pattern | `src/company_bc/equipment_profile/application/services/ai_tiebreaker.py` | Pattern only | Different interface — chat vs. select. Reuse the ABC + factory approach |
| Groq via OpenAI SDK | Same file (`GroqAdapter`) | Pattern only | Groq uses `openai.OpenAI(base_url="https://api.groq.com/openai/v1")` — same approach |
| AI settings | `core/config.py` → `AISettings` | Yes | Add `ANTHROPIC_API_KEY`, `AI_SUPPORT_PROVIDER`, `AI_SUPPORT_MODEL` fields |
| Rate limiting pattern | `src/auth_bc/magic_link/application/commands/create_magic_link.py` | Pattern only | Same concept: count + threshold → exception. We use Redis instead of DB |
| Auth dependencies | `adapters/http/api/auth/dependencies.py` | Yes | Reuse `require_role(UserRole.TECHNICIAN)` — TECHNICIAN role includes ADMIN (hierarchy) |
| Help content (i18n) | `web/app/src/locales/en.ts` → 75 `help.*` keys | Read at runtime | Backend reads these keys to build system prompt |
| Company entity | `src/company_bc/company/domain/entities.py` → `Company` | Yes | Read `name`, `plan`, `sector` for system prompt context |
| Nav config (modules) | `src/company_bc/nav_config/` | Yes | Query enabled modules for system prompt |
| Email service pattern | `core/email.py` | Pattern only | Same ABC + factory + dev-fallback pattern for AI providers |
| Help panel (E51) | `web/app/src/components/help/HelpPanel.tsx` | Modify | Add "AI Assistant" button to help panel |

## Implementation Plan

### 1. Domain Layer

#### Interfaces

| Interface | File Path | Description |
|-----------|-----------|-------------|
| `SupportAIProviderInterface` | `src/support_bc/ai_assistant/domain/service.py` | ABC with `chat(messages, system_prompt) -> str` method |

```python
# src/support_bc/ai_assistant/domain/service.py
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

#### Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| `AIProviderError` | `src/support_bc/ai_assistant/domain/exceptions.py` | Base exception for provider failures |
| `AIRateLimitExceededError` | Same file | User exceeded 20 queries/hour |
| `AIUnavailableError` | Same file | Both providers failed |

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

### 2. Infrastructure Layer

#### Provider Implementations

| Implementation | File Path | Description |
|----------------|-----------|-------------|
| `AnthropicProvider` | `src/support_bc/ai_assistant/infrastructure/anthropic_provider.py` | Uses `anthropic` SDK |
| `GroqProvider` | `src/support_bc/ai_assistant/infrastructure/groq_provider.py` | Uses `openai` SDK with Groq base URL |
| `get_ai_provider` | `src/support_bc/ai_assistant/infrastructure/provider_factory.py` | Factory function |

```python
# src/support_bc/ai_assistant/infrastructure/anthropic_provider.py
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

```python
# src/support_bc/ai_assistant/infrastructure/groq_provider.py
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

```python
# src/support_bc/ai_assistant/infrastructure/provider_factory.py
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
    # Default: groq
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

#### System Prompt Builder

| Component | File Path | Description |
|-----------|-----------|-------------|
| `build_system_prompt` | `src/support_bc/ai_assistant/infrastructure/system_prompt.py` | Builds system prompt from help content + company context |

```python
# src/support_bc/ai_assistant/infrastructure/system_prompt.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Help content cache (loaded once at import time)
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
        import re
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

### 3. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `AIChatCommand` | `AIChatCommandHandler` | `src/support_bc/ai_assistant/application/commands/ai_chat.py` | Process AI chat message with rate limiting + failover |

```python
# src/support_bc/ai_assistant/application/commands/ai_chat.py
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
    messages: list[dict[str, str]]  # [{"role": "user"|"assistant", "content": "..."}]


class AIChatCommandHandler(CommandHandler[AIChatCommand]):
    """Handle AI chat with rate limiting and provider failover.

    Note: This handler stores the AI response in `self.response` after execution.
    The router reads this value after calling handle(). This is necessary because
    CQRS commands return None, but we need the AI response for the HTTP response.
    """

    MAX_QUERIES_PER_HOUR = 20

    def __init__(
        self,
        primary_provider: SupportAIProviderInterface,
        fallback_provider: SupportAIProviderInterface,
        redis_client,  # redis.Redis
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.redis = redis_client
        self.response: str = ""  # Set after handle()

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
        pipe.expire(rate_key, 3600)  # 1 hour TTL
        pipe.execute()
```

### 4. HTTP Layer

#### Endpoints

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| `POST` | `/api/v1/my/ai-support` | Send message to AI, get response | TECHNICIAN+ (includes ADMIN) |

#### Router

```python
# adapters/http/api/my/ai_support_router.py
import redis
from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.my.schemas import AIChatRequest, AIChatResponse
from core.config import settings
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
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


def _get_redis():
    return redis.Redis.from_url(settings.celery.CELERY_BROKER_URL, decode_responses=True)


@router.post("/ai-support", status_code=status.HTTP_200_OK)
def ai_chat(
    body: AIChatRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
):
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
                company_name=current_user.company_name if hasattr(current_user, 'company_name') else "",
                plan_tier=current_user.plan_tier if hasattr(current_user, 'plan_tier') else "free",
                enabled_modules=current_user.enabled_modules if hasattr(current_user, 'enabled_modules') else [],
                messages=body.messages,
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

**Note on company context:** The router needs company name, plan tier, and enabled modules. Rather than adding these to the User entity, the router will fetch them from the company repository and nav config. The final implementation will inject a dependency that resolves company context:

```python
# adapters/http/api/my/dependencies.py (addition)
from sqlalchemy.orm import Session
from fastapi import Depends
from core.database import get_db
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.company_bc.nav_config.infrastructure.repository import NavConfigRepository

@dataclass
class CompanyContext:
    name: str
    plan_tier: str
    enabled_modules: list[str]

def get_company_context(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
) -> CompanyContext:
    """Resolve company context for the current user."""
    company = CompanyRepository(db).find_by_id(current_user.company_id)
    nav_config = NavConfigRepository(db).find_by_company(current_user.company_id)
    return CompanyContext(
        name=company.name if company else "",
        plan_tier=company.plan.value if company else "free",
        enabled_modules=nav_config.enabled_modules if nav_config else [],
    )
```

#### Schemas

```python
# adapters/http/api/my/schemas.py (additions)
from pydantic import BaseModel, Field

class AIChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)

class AIChatRequest(BaseModel):
    messages: list[AIChatMessage] = Field(..., min_length=1, max_length=50)

class AIChatResponse(BaseModel):
    response: str
```

### 5. Frontend Components

#### Component Structure

```
web/app/src/
├── components/
│   └── support/
│       ├── AIChatWidget.tsx      # Floating button + slide-in panel
│       └── AIChatMessage.tsx     # Individual message bubble
├── hooks/
│   └── useAIChat.ts              # Chat state + API call hook
└── locales/
    ├── en.ts                     # Add ai_chat.* keys
    └── es.ts                     # Add ai_chat.* keys
```

#### AIChatWidget.tsx

- Floating button (bottom-right, next to help button) — visible only for ADMIN/TECHNICIAN
- Slide-in panel from the right (similar to HelpPanel pattern)
- Message list with auto-scroll
- Input field with send button
- Loading indicator while AI responds
- "Create support ticket" button (disabled, with "Coming soon" tooltip)
- Rate limit exceeded message when 429 received
- "AI unavailable" fallback when 503 received

#### useAIChat.ts

- Manages `messages` array in React state (session-scoped)
- `sendMessage(content: string)` → appends user message, calls API with full history, appends AI response
- Handles loading state, error state, rate limit state
- Clears on unmount or explicit reset

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `core/config.py` → `AISettings` | Add fields | `ANTHROPIC_API_KEY: str = ""`, `AI_SUPPORT_PROVIDER: str = "groq"`, `AI_SUPPORT_MODEL: str = ""` |
| `pyproject.toml` | Add dependency | `anthropic` SDK (Groq uses `openai` which is already present) |
| `app.py` | Add router | `application.include_router(ai_support_router)` |
| `web/app/src/components/help/HelpPanel.tsx` | Add link | "AI Assistant" button in help panel |
| `web/app/src/App.tsx` or layout | Add widget | Render `<AIChatWidget />` for ADMIN/TECHNICIAN |
| `web/app/src/locales/en.ts` | Add keys | `ai_chat.title`, `ai_chat.placeholder`, `ai_chat.disclaimer`, etc. |
| `web/app/src/locales/es.ts` | Add keys | Spanish translations for same keys |
| `.env.example` | Add vars | `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `AI_SUPPORT_PROVIDER`, `AI_SUPPORT_MODEL` |

#### Breaking Changes

None — this is a new feature with new endpoints. No existing functionality is modified.

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `anthropic` | Python package | Anthropic SDK for Claude API |
| `openai` | Python package | Already installed; used for Groq via OpenAI-compatible API |
| Redis | Infrastructure | Already running (Celery broker); used for rate limiting |
| Company entity | Cross-BC read | Read company name + plan for system prompt context |
| Nav config | Cross-BC read | Read enabled modules for system prompt context |

## Testing Strategy

| Test Type | Scope | File Path | Priority |
|-----------|-------|-----------|----------|
| Unit | `AIChatCommandHandler` — rate limiting, failover, response capture | `tests/unit/support_bc/ai_assistant/test_ai_chat.py` | High |
| Unit | `AnthropicProvider` — mock SDK, verify call structure | `tests/unit/support_bc/ai_assistant/test_anthropic_provider.py` | Medium |
| Unit | `GroqProvider` — mock SDK, verify call structure | `tests/unit/support_bc/ai_assistant/test_groq_provider.py` | Medium |
| Unit | `build_system_prompt` — verify output includes company context | `tests/unit/support_bc/ai_assistant/test_system_prompt.py` | Medium |
| Unit | `get_ai_provider` / `get_fallback_provider` — config-based selection | `tests/unit/support_bc/ai_assistant/test_provider_factory.py` | Low |
| Integration | `POST /my/ai-support` — 200 success, 429 rate limit, 503 unavailable, 403 wrong role | `tests/integration/test_ai_support_endpoints.py` | High |

### Key Test Scenarios

1. **Rate limiting:** Mock Redis, verify 429 when count >= 20
2. **Primary success:** Mock provider returns response, verify handler.response is set
3. **Failover:** Primary raises `AIProviderError`, fallback succeeds, verify response
4. **Both fail:** Both raise `AIProviderError`, verify `AIUnavailableError` raised
5. **Auth:** EMPLOYEE role gets 403, TECHNICIAN and ADMIN get 200
6. **Message validation:** Empty messages → 422, role not user/assistant → 422, content too long → 422
7. **System prompt:** Verify company name, plan tier, enabled modules appear in prompt
8. **Redis increment:** Verify counter is incremented on success, NOT incremented on failure

## Implementation Order

1. [ ] Domain: `SupportAIProviderInterface` + exceptions
2. [ ] Infrastructure: `AnthropicProvider`, `GroqProvider`, `provider_factory`
3. [ ] Infrastructure: `build_system_prompt`
4. [ ] Application: `AIChatCommand` + `AIChatCommandHandler`
5. [ ] Configuration: Add fields to `AISettings` in `core/config.py`
6. [ ] Configuration: Add `anthropic` to `pyproject.toml`
7. [ ] HTTP: Schemas (`AIChatRequest`, `AIChatResponse`) + router + company context dependency
8. [ ] HTTP: Register router in `app.py`
9. [ ] Tests: Unit tests for handler, providers, system prompt
10. [ ] Tests: Integration tests for endpoint
11. [ ] Frontend: `useAIChat` hook
12. [ ] Frontend: `AIChatWidget` + `AIChatMessage` components
13. [ ] Frontend: i18n keys (en.ts + es.ts)
14. [ ] Frontend: Mount widget in app layout
15. [ ] Collateral: Add "AI Assistant" link to HelpPanel
16. [ ] Collateral: Update `.env.example`

## Folder Structure (New Files)

```
src/support_bc/
├── __init__.py
└── ai_assistant/
    ├── __init__.py
    ├── domain/
    │   ├── __init__.py
    │   ├── service.py              # SupportAIProviderInterface (ABC)
    │   └── exceptions.py           # AIProviderError, AIRateLimitExceededError, AIUnavailableError
    ├── application/
    │   ├── __init__.py
    │   └── commands/
    │       ├── __init__.py
    │       └── ai_chat.py          # AIChatCommand + AIChatCommandHandler
    └── infrastructure/
        ├── __init__.py
        ├── anthropic_provider.py   # AnthropicProvider
        ├── groq_provider.py        # GroqProvider
        ├── provider_factory.py     # get_ai_provider(), get_fallback_provider()
        └── system_prompt.py        # build_system_prompt()

adapters/http/api/my/
├── ai_support_router.py            # POST /api/v1/my/ai-support
└── schemas.py                      # AIChatRequest, AIChatResponse (additions)

web/app/src/
├── components/support/
│   ├── AIChatWidget.tsx
│   └── AIChatMessage.tsx
└── hooks/
    └── useAIChat.ts
```

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| AI provider downtime | Medium | Medium | Failover to secondary provider; fallback error message |
| Help content too large for system prompt | Low | Low | 75 help keys ≈ 3-4K tokens — well within context limits |
| Rate limit bypass via multiple tabs | Low | Low | Redis counter is per-user, not per-session — all tabs share the same limit |
| Groq model deprecation | Low | Medium | Model is configurable via env var; switch without code change |
| Anthropic SDK breaking changes | Low | Medium | Pin SDK version in pyproject.toml |

## Open Technical Questions

None — all decisions are resolved.
