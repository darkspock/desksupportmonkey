import logging

from src.support_bc.ai_assistant.domain.exceptions import AIProviderError
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface

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
