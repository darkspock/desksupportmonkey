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

        # 2. Classify help keys for relevance, then build system prompt
        from src.support_bc.ai_assistant.infrastructure.system_prompt import (
            build_system_prompt,
            select_relevant_help_keys,
        )

        last_user_message = ""
        for msg in reversed(command.messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

        relevant_keys = select_relevant_help_keys(last_user_message)

        system_prompt = build_system_prompt(
            company_name=command.company_name,
            plan_tier=command.plan_tier,
            enabled_modules=command.enabled_modules,
            relevant_keys=relevant_keys,
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
