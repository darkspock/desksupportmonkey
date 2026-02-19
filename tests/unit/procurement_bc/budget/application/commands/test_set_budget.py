import pytest
from unittest.mock import MagicMock

from src.procurement_bc.budget.application.commands.set_budget import (
    SetDepartmentBudgetCommand,
    SetDepartmentBudgetCommandHandler,
)
from src.procurement_bc.budget.domain.entities import DepartmentBudget


class TestSetDepartmentBudgetCommandHandler:
    def setup_method(self):
        self.budget_repo = MagicMock()
        self.handler = SetDepartmentBudgetCommandHandler(
            budget_repo=self.budget_repo,
        )

    def test_set_new_budget(self):
        self.budget_repo.find_by_department_year.return_value = None

        self.handler.handle(
            SetDepartmentBudgetCommand(
                company_id="c1",
                department_id="d1",
                fiscal_year=2026,
                allocated_amount_cents=500000,
                performed_by="admin1",
            )
        )

        self.budget_repo.save.assert_called_once()
        saved = self.budget_repo.save.call_args[0][0]
        assert isinstance(saved, DepartmentBudget)
        assert saved.allocated_amount_cents == 500000

    def test_update_existing_budget(self):
        existing = DepartmentBudget.create(
            company_id="c1",
            department_id="d1",
            fiscal_year=2026,
            allocated_amount_cents=300000,
        )
        self.budget_repo.find_by_department_year.return_value = existing

        self.handler.handle(
            SetDepartmentBudgetCommand(
                company_id="c1",
                department_id="d1",
                fiscal_year=2026,
                allocated_amount_cents=700000,
                performed_by="admin1",
            )
        )

        self.budget_repo.save.assert_called_once()
        assert existing.allocated_amount_cents == 700000

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="negative"):
            self.handler.handle(
                SetDepartmentBudgetCommand(
                    company_id="c1",
                    department_id="d1",
                    fiscal_year=2026,
                    allocated_amount_cents=-100,
                    performed_by="admin1",
                )
            )
