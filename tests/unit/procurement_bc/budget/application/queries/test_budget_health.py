from unittest.mock import MagicMock

from src.procurement_bc.budget.application.queries.get_budget_health import (
    GetBudgetHealthQuery,
    GetBudgetHealthQueryHandler,
)
from src.procurement_bc.budget.domain.entities import (
    DepartmentBudget,
)


class TestGetBudgetHealthQueryHandler:
    def setup_method(self):
        self.budget_repo = MagicMock()
        self.budget_checker = MagicMock()
        self.budget_checker.config_repo = MagicMock()
        self.budget_checker.config_repo.find_by_company_id.return_value = None
        self.budget_checker.get_fiscal_year.return_value = 2026

        self.handler = GetBudgetHealthQueryHandler(
            budget_repo=self.budget_repo,
            budget_checker=self.budget_checker,
        )

    def test_returns_totals_with_at_risk(self):
        budgets = [
            DepartmentBudget.create(
                company_id="comp1",
                department_id="dept1",
                fiscal_year=2026,
                allocated_amount_cents=100000,
            ),
            DepartmentBudget.create(
                company_id="comp1",
                department_id="dept2",
                fiscal_year=2026,
                allocated_amount_cents=50000,
            ),
        ]
        self.budget_repo.find_all_by_company_year.return_value = budgets
        # dept1: 90% spent (at risk), dept2: 40% spent
        self.budget_checker.compute_spending.side_effect = [90000, 20000]

        result = self.handler.handle(
            GetBudgetHealthQuery(company_id="comp1", fiscal_year=2026)
        )

        assert result.total_allocated_cents == 150000
        assert result.total_spent_cents == 110000
        assert len(result.departments_at_risk) == 1
        assert result.departments_at_risk[0].department_id == "dept1"
        assert result.departments_at_risk[0].utilization_pct == 90.0

    def test_no_budgets_returns_empty(self):
        self.budget_repo.find_all_by_company_year.return_value = []

        result = self.handler.handle(
            GetBudgetHealthQuery(company_id="comp1", fiscal_year=2026)
        )

        assert result.total_allocated_cents == 0
        assert result.total_spent_cents == 0
        assert result.departments_at_risk == []

    def test_all_below_threshold(self):
        budgets = [
            DepartmentBudget.create(
                company_id="comp1",
                department_id="dept1",
                fiscal_year=2026,
                allocated_amount_cents=100000,
            ),
        ]
        self.budget_repo.find_all_by_company_year.return_value = budgets
        self.budget_checker.compute_spending.return_value = 50000

        result = self.handler.handle(
            GetBudgetHealthQuery(company_id="comp1", fiscal_year=2026)
        )

        assert len(result.departments_at_risk) == 0
        assert result.total_spent_cents == 50000

    def test_uses_fiscal_year_from_config_when_not_provided(self):
        self.budget_repo.find_all_by_company_year.return_value = []

        self.handler.handle(
            GetBudgetHealthQuery(company_id="comp1")
        )

        # Verify config_repo was consulted to determine fiscal year
        self.budget_checker.config_repo.find_by_company_id.assert_called_once_with("comp1")
        self.budget_repo.find_all_by_company_year.assert_called_once()
