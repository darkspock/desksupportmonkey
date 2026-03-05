import logging

from src.support_bc.ai_assistant.domain.exceptions import AIProviderError
from src.support_bc.ai_assistant.domain.service import SupportAIProviderInterface

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
