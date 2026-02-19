from dataclasses import dataclass
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
class DepartmentBudgetResult:
    budget_id: Optional[str]
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    spent_cents: int
    remaining_cents: int
    utilization_pct: float
    currency: str


@dataclass
class GetDepartmentBudgetQuery(Query):
    company_id: str
    department_id: str
    fiscal_year: Optional[int] = None


class GetDepartmentBudgetQueryHandler(
    QueryHandler[
        GetDepartmentBudgetQuery,
        Optional[DepartmentBudgetResult],
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
        self,
        query: GetDepartmentBudgetQuery,
    ) -> Optional[DepartmentBudgetResult]:
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

        budget = self.budget_repo.find_by_department_year(
            query.department_id, fiscal_year,
            query.company_id,
        )

        if not budget:
            return None

        spent = self.budget_checker.compute_spending(
            query.company_id,
            query.department_id,
            fiscal_year,
        )
        allocated = budget.allocated_amount_cents
        remaining = allocated - spent
        utilization = (
            (spent / allocated * 100) if allocated > 0
            else 0.0
        )

        return DepartmentBudgetResult(
            budget_id=budget.id,
            department_id=budget.department_id,
            fiscal_year=fiscal_year,
            allocated_amount_cents=allocated,
            spent_cents=spent,
            remaining_cents=remaining,
            utilization_pct=round(utilization, 2),
            currency=budget.currency,
        )
