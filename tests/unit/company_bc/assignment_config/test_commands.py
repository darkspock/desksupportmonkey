"""Tests for SaveCompanyAIConfigCommandHandler."""

from unittest.mock import MagicMock

import pytest

from src.company_bc.assignment_config.application.commands.save_config import (  # noqa: E501
    InvalidProviderError,
    SaveCompanyAIConfigCommand,
    SaveCompanyAIConfigCommandHandler,
)
from src.company_bc.assignment_config.domain.entities import (
    CompanyAssignmentAIConfig,
)
from src.company_bc.assignment_config.domain.enums import (
    AIProvider,
)


class TestSaveConfig:
    def test_save_config_creates_new(self):
        """First save creates a new config."""
        repo = MagicMock()
        repo.find_by_company.return_value = None

        handler = SaveCompanyAIConfigCommandHandler(
            config_repo=repo,
        )
        handler.handle(
            SaveCompanyAIConfigCommand(
                company_id="c1",
                provider="openai",
                prompt_template="Pick the best asset.",
                performed_by="u1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.company_id == "c1"
        assert saved.provider == AIProvider.OPENAI
        assert saved.prompt_template == "Pick the best asset."

    def test_save_config_updates_existing(self):
        """Second save updates existing config."""
        existing = CompanyAssignmentAIConfig.create(
            company_id="c1",
            provider=AIProvider.OPENAI,
            prompt_template="old prompt",
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing

        handler = SaveCompanyAIConfigCommandHandler(
            config_repo=repo,
        )
        handler.handle(
            SaveCompanyAIConfigCommand(
                company_id="c1",
                provider="groq",
                prompt_template="new prompt",
                performed_by="u1",
            )
        )

        repo.save.assert_called_once()
        assert existing.provider == AIProvider.GROQ
        assert existing.prompt_template == "new prompt"

    def test_save_config_invalid_provider(self):
        """Invalid provider raises error."""
        repo = MagicMock()
        handler = SaveCompanyAIConfigCommandHandler(
            config_repo=repo,
        )
        with pytest.raises(InvalidProviderError):
            handler.handle(
                SaveCompanyAIConfigCommand(
                    company_id="c1",
                    provider="invalid_provider",
                    prompt_template="prompt",
                    performed_by="u1",
                )
            )
