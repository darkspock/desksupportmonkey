from unittest.mock import MagicMock

from src.company_bc.sla_escalation_config.application.commands.save_config import (
    SaveSlaEscalationConfigCommand,
    SaveSlaEscalationConfigCommandHandler,
)
from src.company_bc.sla_escalation_config.domain.entities import (
    CompanySlaEscalationConfig,
)


class TestSaveSlaEscalationConfigCommand:
    def test_creates_new_config_when_none_exists(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveSlaEscalationConfigCommandHandler(config_repo=repo)

        handler.handle(
            SaveSlaEscalationConfigCommand(
                company_id="comp123",
                enabled=True,
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert isinstance(saved, CompanySlaEscalationConfig)
        assert saved.company_id == "comp123"
        assert saved.enabled is True

    def test_updates_existing_config(self):
        existing = CompanySlaEscalationConfig.create(
            company_id="comp123",
            enabled=True,
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = SaveSlaEscalationConfigCommandHandler(config_repo=repo)

        handler.handle(
            SaveSlaEscalationConfigCommand(
                company_id="comp123",
                enabled=False,
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        assert existing.enabled is False

    def test_sets_enabled_to_false(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveSlaEscalationConfigCommandHandler(config_repo=repo)

        handler.handle(
            SaveSlaEscalationConfigCommand(
                company_id="comp123",
                enabled=False,
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.enabled is False

    def test_updates_existing_enabled_to_true(self):
        existing = CompanySlaEscalationConfig.create(
            company_id="comp123",
            enabled=False,
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = SaveSlaEscalationConfigCommandHandler(config_repo=repo)

        handler.handle(
            SaveSlaEscalationConfigCommand(
                company_id="comp123",
                enabled=True,
                performed_by="admin1",
            )
        )

        repo.save.assert_called_once()
        assert existing.enabled is True

    def test_find_by_company_called_with_correct_id(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = SaveSlaEscalationConfigCommandHandler(config_repo=repo)

        handler.handle(
            SaveSlaEscalationConfigCommand(
                company_id="comp456",
                enabled=True,
                performed_by="admin1",
            )
        )

        repo.find_by_company.assert_called_once_with("comp456")
