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
