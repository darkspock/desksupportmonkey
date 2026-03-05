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
