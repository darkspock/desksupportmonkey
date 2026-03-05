from unittest.mock import patch

from src.support_bc.ai_assistant.infrastructure.system_prompt import build_system_prompt


class TestBuildSystemPrompt:
    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt._load_help_content")
    def test_company_context_included(self, mock_load):
        mock_load.return_value = {"help.dashboard": "View your dashboard"}

        result = build_system_prompt(
            company_name="Acme Corp",
            plan_tier="premium",
            enabled_modules=["assets", "requests"],
        )

        assert "Acme Corp" in result
        assert "premium" in result
        assert "assets, requests" in result

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt._load_help_content")
    def test_empty_modules_shows_all(self, mock_load):
        mock_load.return_value = {}

        result = build_system_prompt(
            company_name="Test",
            plan_tier="free",
            enabled_modules=[],
        )

        assert "all modules" in result

    @patch("src.support_bc.ai_assistant.infrastructure.system_prompt._load_help_content")
    def test_help_content_included(self, mock_load):
        mock_load.return_value = {
            "help.assets": "Manage your assets",
            "help.requests": "Submit requests",
        }

        result = build_system_prompt(
            company_name="Test",
            plan_tier="starter",
            enabled_modules=[],
        )

        assert "assets: Manage your assets" in result
        assert "requests: Submit requests" in result
