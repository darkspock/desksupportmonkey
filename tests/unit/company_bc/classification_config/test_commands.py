"""Tests for classification config save command and get query."""

from unittest.mock import MagicMock

import pytest

from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.classification_config.application.commands.save_config import (
    InvalidProviderError,
    InvalidThresholdError,
    InvalidTimeoutError,
    SaveClassificationConfigCommand,
    SaveClassificationConfigCommandHandler,
)
from src.company_bc.classification_config.application.queries.get_config import (
    GetClassificationConfigQuery,
    GetClassificationConfigQueryHandler,
)
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)


class TestSaveClassificationConfig:
    def test_creates_new_config(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None

        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        handler.handle(
            SaveClassificationConfigCommand(
                company_id="c1",
                is_enabled=True,
                provider="openai",
                confidence_threshold=0.8,
                timeout_seconds=15,
                model="gpt-4o-mini",
                prompt_template="Be precise.",
                performed_by="u1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.company_id == "c1"
        assert saved.is_enabled is True
        assert saved.provider == AIProvider.OPENAI
        assert saved.model == "gpt-4o-mini"
        assert saved.confidence_threshold == 0.8
        assert saved.prompt_template == "Be precise."
        assert saved.timeout_seconds == 15

    def test_updates_existing_config(self):
        existing = CompanyClassificationConfig.create(
            company_id="c1",
            is_enabled=False,
            provider=AIProvider.OPENAI,
            confidence_threshold=0.7,
            timeout_seconds=10,
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing

        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        handler.handle(
            SaveClassificationConfigCommand(
                company_id="c1",
                is_enabled=True,
                provider="groq",
                confidence_threshold=0.9,
                timeout_seconds=30,
                performed_by="u1",
            )
        )

        repo.save.assert_called_once()
        assert existing.is_enabled is True
        assert existing.provider == AIProvider.GROQ
        assert existing.confidence_threshold == 0.9
        assert existing.timeout_seconds == 30

    def test_invalid_provider_raises(self):
        repo = MagicMock()
        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        with pytest.raises(InvalidProviderError):
            handler.handle(
                SaveClassificationConfigCommand(
                    company_id="c1",
                    is_enabled=True,
                    provider="invalid",
                    confidence_threshold=0.7,
                    timeout_seconds=10,
                    performed_by="u1",
                )
            )

    def test_invalid_threshold_too_low_raises(self):
        repo = MagicMock()
        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        with pytest.raises(InvalidThresholdError):
            handler.handle(
                SaveClassificationConfigCommand(
                    company_id="c1",
                    is_enabled=True,
                    provider="openai",
                    confidence_threshold=0.3,
                    timeout_seconds=10,
                    performed_by="u1",
                )
            )

    def test_invalid_threshold_too_high_raises(self):
        repo = MagicMock()
        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        with pytest.raises(InvalidThresholdError):
            handler.handle(
                SaveClassificationConfigCommand(
                    company_id="c1",
                    is_enabled=True,
                    provider="openai",
                    confidence_threshold=1.5,
                    timeout_seconds=10,
                    performed_by="u1",
                )
            )

    def test_invalid_timeout_raises(self):
        repo = MagicMock()
        handler = SaveClassificationConfigCommandHandler(config_repo=repo)
        with pytest.raises(InvalidTimeoutError):
            handler.handle(
                SaveClassificationConfigCommand(
                    company_id="c1",
                    is_enabled=True,
                    provider="openai",
                    confidence_threshold=0.7,
                    timeout_seconds=0,
                    performed_by="u1",
                )
            )


class TestGetClassificationConfig:
    def test_returns_dto_when_found(self):
        config = CompanyClassificationConfig.create(
            company_id="c1",
            is_enabled=True,
            provider=AIProvider.OPENAI,
            confidence_threshold=0.8,
            timeout_seconds=15,
            model="gpt-4o-mini",
            prompt_template="Be strict.",
        )
        repo = MagicMock()
        repo.find_by_company.return_value = config

        handler = GetClassificationConfigQueryHandler(config_repo=repo)
        result = handler.handle(
            GetClassificationConfigQuery(company_id="c1")
        )

        assert result is not None
        assert result.company_id == "c1"
        assert result.is_enabled is True
        assert result.provider == "openai"
        assert result.model == "gpt-4o-mini"
        assert result.confidence_threshold == 0.8
        assert result.prompt_template == "Be strict."
        assert result.timeout_seconds == 15

    def test_returns_none_when_not_found(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None

        handler = GetClassificationConfigQueryHandler(config_repo=repo)
        result = handler.handle(
            GetClassificationConfigQuery(company_id="c1")
        )

        assert result is None
