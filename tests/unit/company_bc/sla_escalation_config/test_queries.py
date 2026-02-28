from unittest.mock import MagicMock

from src.company_bc.sla_escalation_config.application.queries.get_config import (
    GetSlaEscalationConfigQuery,
    GetSlaEscalationConfigQueryHandler,
    SlaEscalationConfigDto,
)
from src.company_bc.sla_escalation_config.domain.entities import (
    CompanySlaEscalationConfig,
)


class TestGetSlaEscalationConfigQuery:
    def test_returns_existing_config_enabled_true(self):
        existing = CompanySlaEscalationConfig.create(
            company_id="comp123",
            enabled=True,
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = GetSlaEscalationConfigQueryHandler(config_repo=repo)

        result = handler.handle(
            GetSlaEscalationConfigQuery(company_id="comp123")
        )

        assert isinstance(result, SlaEscalationConfigDto)
        assert result.enabled is True

    def test_returns_existing_config_enabled_false(self):
        existing = CompanySlaEscalationConfig.create(
            company_id="comp123",
            enabled=False,
        )
        repo = MagicMock()
        repo.find_by_company.return_value = existing
        handler = GetSlaEscalationConfigQueryHandler(config_repo=repo)

        result = handler.handle(
            GetSlaEscalationConfigQuery(company_id="comp123")
        )

        assert isinstance(result, SlaEscalationConfigDto)
        assert result.enabled is False

    def test_returns_default_enabled_true_when_no_config(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = GetSlaEscalationConfigQueryHandler(config_repo=repo)

        result = handler.handle(
            GetSlaEscalationConfigQuery(company_id="comp123")
        )

        assert isinstance(result, SlaEscalationConfigDto)
        assert result.enabled is True

    def test_find_by_company_called_with_correct_id(self):
        repo = MagicMock()
        repo.find_by_company.return_value = None
        handler = GetSlaEscalationConfigQueryHandler(config_repo=repo)

        handler.handle(
            GetSlaEscalationConfigQuery(company_id="comp789")
        )

        repo.find_by_company.assert_called_once_with("comp789")
