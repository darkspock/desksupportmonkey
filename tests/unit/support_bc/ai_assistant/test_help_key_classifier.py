from unittest.mock import MagicMock, patch

from src.support_bc.ai_assistant.infrastructure.help_key_classifier import (
    classify_help_keys,
)

SAMPLE_KEYS = {
    "help.default": "Welcome to DSM Control",
    "help.assets": "Manage your IT assets",
    "help.requests": "Submit and track requests",
    "help.dashboard": "View your dashboard",
    "help.reports": "Generate reports",
    "help.users": "Manage users and roles",
    "help.departments": "Organize by department",
    "help.settings": "Configure your workspace",
}


class TestClassifyHelpKeys:
    @patch(
        "src.support_bc.ai_assistant.infrastructure.help_key_classifier._call_classifier"
    )
    def test_success_filters_keys(self, mock_call):
        mock_call.return_value = ["help.assets", "help.requests", "help.dashboard"]

        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "gsk-key")

        assert "help.assets" in result
        assert "help.requests" in result
        assert "help.dashboard" in result
        # help.default always included
        assert "help.default" in result
        # Keys not selected are excluded
        assert "help.reports" not in result
        assert "help.users" not in result

    @patch(
        "src.support_bc.ai_assistant.infrastructure.help_key_classifier._call_classifier"
    )
    def test_always_includes_default(self, mock_call):
        mock_call.return_value = ["help.assets", "help.requests"]

        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "gsk-key")

        assert "help.default" in result

    @patch(
        "src.support_bc.ai_assistant.infrastructure.help_key_classifier._call_classifier"
    )
    def test_fallback_on_exception(self, mock_call):
        mock_call.return_value = None

        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "gsk-key")

        assert result is SAMPLE_KEYS

    @patch(
        "src.support_bc.ai_assistant.infrastructure.help_key_classifier._call_classifier"
    )
    def test_fallback_on_too_few_keys(self, mock_call):
        mock_call.return_value = ["help.nonexistent"]

        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "gsk-key")

        assert result is SAMPLE_KEYS

    def test_no_api_key_returns_all(self):
        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "")

        assert result is SAMPLE_KEYS

    def test_empty_message_returns_all(self):
        result = classify_help_keys(SAMPLE_KEYS, "   ", "gsk-key")

        assert result is SAMPLE_KEYS

    @patch(
        "src.support_bc.ai_assistant.infrastructure.help_key_classifier._call_classifier"
    )
    def test_empty_classifier_response(self, mock_call):
        mock_call.return_value = []

        result = classify_help_keys(SAMPLE_KEYS, "How do I add an asset?", "gsk-key")

        assert result is SAMPLE_KEYS
