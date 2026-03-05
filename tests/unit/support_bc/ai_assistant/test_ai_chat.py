from unittest.mock import MagicMock, call, patch

import pytest

from src.support_bc.ai_assistant.application.commands.ai_chat import (
    AIChatCommand,
    AIChatCommandHandler,
)
from src.support_bc.ai_assistant.domain.exceptions import (
    AIProviderError,
    AIRateLimitExceededError,
    AIUnavailableError,
)


def _make_command(**overrides):
    defaults = {
        "user_id": "user-1",
        "company_id": "company-1",
        "company_name": "Test Corp",
        "plan_tier": "starter",
        "enabled_modules": ["assets", "requests"],
        "messages": [{"role": "user", "content": "How do I create an asset?"}],
    }
    defaults.update(overrides)
    return AIChatCommand(**defaults)


class TestAIChatCommandHandler:
    def setup_method(self):
        self.primary = MagicMock()
        self.fallback = MagicMock()
        self.redis = MagicMock()
        self.redis.get.return_value = None
        self.redis.pipeline.return_value = MagicMock()
        self.handler = AIChatCommandHandler(
            primary_provider=self.primary,
            fallback_provider=self.fallback,
            redis_client=self.redis,
        )

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_primary_success(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.primary.chat.return_value = "Here is how to create an asset."

        self.handler.handle(_make_command())

        assert self.handler.response == "Here is how to create an asset."
        self.primary.chat.assert_called_once()
        self.fallback.chat.assert_not_called()

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_failover_success(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.primary.chat.side_effect = AIProviderError("timeout")
        self.fallback.chat.return_value = "Fallback response."

        self.handler.handle(_make_command())

        assert self.handler.response == "Fallback response."
        self.primary.chat.assert_called_once()
        self.fallback.chat.assert_called_once()

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_both_fail_raises_unavailable(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.primary.chat.side_effect = AIProviderError("timeout")
        self.fallback.chat.side_effect = AIProviderError("also failed")

        with pytest.raises(AIUnavailableError):
            self.handler.handle(_make_command())

    def test_rate_limit_exceeded(self):
        self.redis.get.return_value = "20"

        with pytest.raises(AIRateLimitExceededError):
            self.handler.handle(_make_command())

        self.primary.chat.assert_not_called()
        self.fallback.chat.assert_not_called()

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_rate_limit_not_exceeded(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.redis.get.return_value = "19"
        self.primary.chat.return_value = "Response."

        self.handler.handle(_make_command())

        assert self.handler.response == "Response."

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_redis_counter_incremented_on_success(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.primary.chat.return_value = "Response."
        pipe = MagicMock()
        self.redis.pipeline.return_value = pipe

        self.handler.handle(_make_command(user_id="user-42"))

        pipe.incr.assert_called_once_with("ai_chat_rate:user-42")
        pipe.expire.assert_called_once_with("ai_chat_rate:user-42", 3600)
        pipe.execute.assert_called_once()

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_counter_not_incremented_on_failure(self, mock_prompt):
        mock_prompt.return_value = "system prompt"
        self.primary.chat.side_effect = AIProviderError("fail")
        self.fallback.chat.side_effect = AIProviderError("fail")

        with pytest.raises(AIUnavailableError):
            self.handler.handle(_make_command())

        self.redis.pipeline.assert_not_called()

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.select_relevant_help_keys")
    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt.build_system_prompt")
    def test_classifier_called_with_last_user_message(self, mock_prompt, mock_select):
        mock_select.return_value = {"help.assets": "Manage assets", "help.default": "Welcome"}
        mock_prompt.return_value = "system prompt"
        self.primary.chat.return_value = "Response."

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How do I add an asset?"},
        ]
        self.handler.handle(_make_command(messages=messages))

        mock_select.assert_called_once_with("How do I add an asset?")
        mock_prompt.assert_called_once_with(
            company_name="Test Corp",
            plan_tier="starter",
            enabled_modules=["assets", "requests"],
            relevant_keys={"help.assets": "Manage assets", "help.default": "Welcome"},
        )
