from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.procurement_bc.budget.application.services.budget_checker import (
    BudgetChecker,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
    DepartmentBudget,
)


class TestBudgetCheckerCheckApproval:
    def setup_method(self):
        self.budget_repo = MagicMock()
        self.po_repo = MagicMock()
        self.config_repo = MagicMock()
        self.checker = BudgetChecker(
            budget_repo=self.budget_repo,
            po_repo=self.po_repo,
            config_repo=self.config_repo,
        )

    def test_warn_mode_over_budget_allowed_with_warning(self):
        config = CompanyProcurementConfig.create(
            company_id="c1",
            enforcement_mode="warn",
            fiscal_year_start_month=1,
        )
        self.config_repo.find_by_company_id.return_value = config
        self.budget_repo.find_by_department_year.return_value = (
            DepartmentBudget.create(
                company_id="c1",
                department_id="d1",
                fiscal_year=2026,
                allocated_amount_cents=100000,
            )
        )
        self.po_repo.sum_totals_by_department_status.return_value = 80000

        result = self.checker.check_approval("c1", "d1", 30000)

        assert result.allowed is True
        assert result.warning is not None
        assert "Over budget" in result.warning

    def test_strict_mode_over_budget_not_allowed(self):
        config = CompanyProcurementConfig.create(
            company_id="c1",
            enforcement_mode="strict",
            fiscal_year_start_month=1,
        )
        self.config_repo.find_by_company_id.return_value = config
        self.budget_repo.find_by_department_year.return_value = (
            DepartmentBudget.create(
                company_id="c1",
                department_id="d1",
                fiscal_year=2026,
                allocated_amount_cents=100000,
            )
        )
        self.po_repo.sum_totals_by_department_status.return_value = 80000

        result = self.checker.check_approval("c1", "d1", 30000)

        assert result.allowed is False
        assert result.warning is not None
        assert "exceeded" in result.warning.lower()

    def test_under_budget_allowed_no_warning(self):
        config = CompanyProcurementConfig.create(
            company_id="c1",
            enforcement_mode="strict",
            fiscal_year_start_month=1,
        )
        self.config_repo.find_by_company_id.return_value = config
        self.budget_repo.find_by_department_year.return_value = (
            DepartmentBudget.create(
                company_id="c1",
                department_id="d1",
                fiscal_year=2026,
                allocated_amount_cents=100000,
            )
        )
        self.po_repo.sum_totals_by_department_status.return_value = 20000

        result = self.checker.check_approval("c1", "d1", 30000)

        assert result.allowed is True
        assert result.warning is None
        assert result.remaining_cents == 50000

    def test_no_budget_set_allowed(self):
        config = CompanyProcurementConfig.create(
            company_id="c1",
            enforcement_mode="strict",
            fiscal_year_start_month=1,
        )
        self.config_repo.find_by_company_id.return_value = config
        self.budget_repo.find_by_department_year.return_value = None

        result = self.checker.check_approval("c1", "d1", 50000)

        assert result.allowed is True
        assert result.warning is None


class TestBudgetCheckerGetFiscalYear:
    @patch("src.procurement_bc.budget.application.services.budget_checker.date")
    def test_start_month_january_returns_current_year(self, mock_date):
        mock_date.today.return_value = date(2026, 6, 15)
        assert BudgetChecker.get_fiscal_year(1) == 2026

    @patch("src.procurement_bc.budget.application.services.budget_checker.date")
    def test_start_month_april_current_march_returns_previous(self, mock_date):
        mock_date.today.return_value = date(2027, 3, 15)
        assert BudgetChecker.get_fiscal_year(4) == 2026

    @patch("src.procurement_bc.budget.application.services.budget_checker.date")
    def test_start_month_april_current_april_returns_current(self, mock_date):
        mock_date.today.return_value = date(2027, 4, 1)
        assert BudgetChecker.get_fiscal_year(4) == 2027


class TestBudgetCheckerCheckThreshold:
    def test_crosses_80_percent(self):
        assert BudgetChecker.check_threshold(
            spent_before=79000,
            spent_after=81000,
            allocated=100000,
        ) is True

    def test_already_past_threshold(self):
        assert BudgetChecker.check_threshold(
            spent_before=85000,
            spent_after=90000,
            allocated=100000,
        ) is False

    def test_stays_below_threshold(self):
        assert BudgetChecker.check_threshold(
            spent_before=60000,
            spent_after=70000,
            allocated=100000,
        ) is False

    def test_zero_allocated_returns_false(self):
        assert BudgetChecker.check_threshold(
            spent_before=0,
            spent_after=100,
            allocated=0,
        ) is False
