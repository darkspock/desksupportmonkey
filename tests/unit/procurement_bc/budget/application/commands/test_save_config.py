import pytest
from unittest.mock import MagicMock

from src.procurement_bc.budget.application.commands.save_config import (
    SaveProcurementConfigCommand,
    SaveProcurementConfigCommandHandler,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)


class TestSaveProcurementConfigCommandHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = SaveProcurementConfigCommandHandler(
            config_repo=self.repo,
        )

    def _cmd(self, **overrides):
        defaults = dict(
            company_id="comp1",
            enforcement_mode="warn",
            approval_threshold_cents=50000,
            po_number_prefix="PO",
            fiscal_year_start_month=1,
            currency="USD",
            auto_create_assets=False,
            performed_by="user1",
        )
        defaults.update(overrides)
        return SaveProcurementConfigCommand(**defaults)

    def test_creates_new_config(self):
        self.repo.find_by_company_id.return_value = None
        self.handler.handle(self._cmd())
        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        assert isinstance(saved, CompanyProcurementConfig)
        assert saved.enforcement_mode == "warn"
        assert saved.approval_threshold_cents == 50000

    def test_updates_existing_config(self):
        existing = CompanyProcurementConfig.create(
            company_id="comp1",
        )
        self.repo.find_by_company_id.return_value = (
            existing
        )
        self.handler.handle(
            self._cmd(
                enforcement_mode="strict",
                approval_threshold_cents=100000,
                currency="EUR",
            )
        )
        self.repo.save.assert_called_once()
        assert existing.enforcement_mode == "strict"
        assert existing.approval_threshold_cents == 100000
        assert existing.currency == "EUR"

    def test_invalid_enforcement_mode_raises(self):
        self.repo.find_by_company_id.return_value = None
        with pytest.raises(ValueError, match="enforcement_mode"):
            self.handler.handle(
                self._cmd(enforcement_mode="invalid")
            )

    def test_negative_threshold_raises(self):
        self.repo.find_by_company_id.return_value = None
        with pytest.raises(ValueError, match="threshold"):
            self.handler.handle(
                self._cmd(approval_threshold_cents=-1)
            )

    def test_invalid_fiscal_month_raises(self):
        self.repo.find_by_company_id.return_value = None
        with pytest.raises(ValueError, match="fiscal_year"):
            self.handler.handle(
                self._cmd(fiscal_year_start_month=0)
            )
        with pytest.raises(ValueError, match="fiscal_year"):
            self.handler.handle(
                self._cmd(fiscal_year_start_month=13)
            )

    def test_empty_prefix_raises(self):
        self.repo.find_by_company_id.return_value = None
        with pytest.raises(ValueError, match="prefix"):
            self.handler.handle(
                self._cmd(po_number_prefix="")
            )

    def test_invalid_currency_raises(self):
        self.repo.find_by_company_id.return_value = None
        with pytest.raises(ValueError, match="currency"):
            self.handler.handle(
                self._cmd(currency="US")
            )
