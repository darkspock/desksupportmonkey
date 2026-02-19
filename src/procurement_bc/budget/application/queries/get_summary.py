from dataclasses import dataclass, field
from typing import Optional

from src.procurement_bc.budget.application.services.budget_checker import (
    BudgetChecker,
)
from src.procurement_bc.budget.domain.repository import (
    DepartmentBudgetRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class DepartmentBudgetSummaryItem:
    department_id: str
    allocated_amount_cents: int
    spent_cents: int
    remaining_cents: int
    utilization_pct: float
    currency: str


@dataclass
class BudgetSummaryResult:
    fiscal_year: int
    total_allocated_cents: int
    total_spent_cents: int
    departments: list[DepartmentBudgetSummaryItem] = (
        field(default_factory=list)
    )


@dataclass
class GetBudgetSummaryQuery(Query):
    company_id: str
    fiscal_year: Optional[int] = None


class GetBudgetSummaryQueryHandler(
    QueryHandler[
        GetBudgetSummaryQuery, BudgetSummaryResult,
    ],
):
    def __init__(
        self,
        budget_repo: DepartmentBudgetRepositoryInterface,
        budget_checker: BudgetChecker,
    ):
        self.budget_repo = budget_repo
        self.budget_checker = budget_checker

    def handle(
        self, query: GetBudgetSummaryQuery,
    ) -> BudgetSummaryResult:
        fiscal_year = query.fiscal_year
        if fiscal_year is None:
            config = (
                self.budget_checker.config_repo
                .find_by_company_id(query.company_id)
            )
            start_month = (
                config.fiscal_year_start_month if config
                else 1
            )
            fiscal_year = BudgetChecker.get_fiscal_year(
                start_month,
            )

        budgets = (
            self.budget_repo.find_all_by_company_year(
                query.company_id, fiscal_year,
            )
        )

        departments: list[DepartmentBudgetSummaryItem] = []
        total_allocated = 0
        total_spent = 0

        for b in budgets:
            spent = self.budget_checker.compute_spending(
                query.company_id,
                b.department_id,
                fiscal_year,
            )
            allocated = b.allocated_amount_cents
            remaining = allocated - spent
            utilization = (
                (spent / allocated * 100)
                if allocated > 0
                else 0.0
            )
            departments.append(
                DepartmentBudgetSummaryItem(
                    department_id=b.department_id,
                    allocated_amount_cents=allocated,
                    spent_cents=spent,
                    remaining_cents=remaining,
                    utilization_pct=round(utilization, 2),
                    currency=b.currency,
                )
            )
            total_allocated += allocated
            total_spent += spent

        return BudgetSummaryResult(
            fiscal_year=fiscal_year,
            total_allocated_cents=total_allocated,
            total_spent_cents=total_spent,
            departments=departments,
        )
