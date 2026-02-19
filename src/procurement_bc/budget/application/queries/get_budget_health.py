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


AT_RISK_THRESHOLD_PCT = 80


@dataclass
class AtRiskDepartment:
    department_id: str
    utilization_pct: float
    remaining_cents: int


@dataclass
class BudgetHealthResult:
    total_allocated_cents: int
    total_spent_cents: int
    departments_at_risk: list[AtRiskDepartment] = (
        field(default_factory=list)
    )


@dataclass
class GetBudgetHealthQuery(Query):
    company_id: str
    fiscal_year: Optional[int] = None


class GetBudgetHealthQueryHandler(
    QueryHandler[
        GetBudgetHealthQuery, BudgetHealthResult,
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
        self, query: GetBudgetHealthQuery,
    ) -> BudgetHealthResult:
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

        total_allocated = 0
        total_spent = 0
        at_risk: list[AtRiskDepartment] = []

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
            total_allocated += allocated
            total_spent += spent

            if utilization >= AT_RISK_THRESHOLD_PCT:
                at_risk.append(
                    AtRiskDepartment(
                        department_id=b.department_id,
                        utilization_pct=round(utilization, 2),
                        remaining_cents=remaining,
                    )
                )

        return BudgetHealthResult(
            total_allocated_cents=total_allocated,
            total_spent_cents=total_spent,
            departments_at_risk=at_risk,
        )
