from unittest.mock import MagicMock

from src.procurement_bc.budget.application.queries.get_config import (
    GetProcurementConfigQuery,
    GetProcurementConfigQueryHandler,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)


class TestGetProcurementConfigQueryHandler:
    def test_returns_existing_config(self):
        repo = MagicMock()
        config = CompanyProcurementConfig.create(
            company_id="comp1",
            enforcement_mode="strict",
            approval_threshold_cents=10000,
        )
        repo.find_by_company_id.return_value = config

        handler = GetProcurementConfigQueryHandler(
            config_repo=repo,
        )
        result = handler.handle(
            GetProcurementConfigQuery(
                company_id="comp1",
            )
        )
        assert result.enforcement_mode == "strict"
        assert result.approval_threshold_cents == 10000

    def test_returns_defaults_when_not_found(self):
        repo = MagicMock()
        repo.find_by_company_id.return_value = None

        handler = GetProcurementConfigQueryHandler(
            config_repo=repo,
        )
        result = handler.handle(
            GetProcurementConfigQuery(
                company_id="comp1",
            )
        )
        assert result.company_id == "comp1"
        assert result.enforcement_mode == "warn"
        assert result.approval_threshold_cents == 0
        assert result.po_number_prefix == "PO"
        assert result.fiscal_year_start_month == 1
        assert result.currency == "USD"
        assert result.auto_create_assets is False
