import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
    DepartmentBudgetRepositoryInterface,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)

COUNTABLE_STATUSES = [
    s.value
    for s in PurchaseOrderStatus
    if s.is_countable_for_budget
]

THRESHOLD_PCT = 80


@dataclass
class BudgetCheckResult:
    allowed: bool
    warning: Optional[str]
    remaining_cents: int
    spent_cents: int
    allocated_cents: int


class BudgetChecker:
    def __init__(
        self,
        budget_repo: DepartmentBudgetRepositoryInterface,
        po_repo: PurchaseOrderRepositoryInterface,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        self.budget_repo = budget_repo
        self.po_repo = po_repo
        self.config_repo = config_repo

    def check_approval(
        self,
        company_id: str,
        department_id: str,
        po_total_cents: int,
    ) -> BudgetCheckResult:
        config = self.config_repo.find_by_company_id(
            company_id,
        )
        if not config:
            config = CompanyProcurementConfig.defaults(
                company_id,
            )

        fiscal_year = self.get_fiscal_year(
            config.fiscal_year_start_month,
        )
        budget = self.budget_repo.find_by_department_year(
            department_id, fiscal_year, company_id,
        )

        if not budget:
            return BudgetCheckResult(
                allowed=True,
                warning=None,
                remaining_cents=0,
                spent_cents=0,
                allocated_cents=0,
            )

        spent = self.compute_spending(
            company_id, department_id, fiscal_year, config,
        )
        new_total = spent + po_total_cents
        remaining = budget.allocated_amount_cents - new_total
        allocated = budget.allocated_amount_cents

        if new_total > allocated:
            shortfall = new_total - allocated
            if config.enforcement_mode == "strict":
                return BudgetCheckResult(
                    allowed=False,
                    warning=(
                        f"Budget exceeded by "
                        f"${shortfall / 100:.2f}. "
                        f"Allocated: "
                        f"${allocated / 100:.2f}, "
                        f"Would spend: "
                        f"${new_total / 100:.2f}"
                    ),
                    remaining_cents=remaining,
                    spent_cents=spent,
                    allocated_cents=allocated,
                )
            else:
                return BudgetCheckResult(
                    allowed=True,
                    warning=(
                        f"Over budget by "
                        f"${shortfall / 100:.2f}. "
                        f"Allocated: "
                        f"${allocated / 100:.2f}, "
                        f"Would spend: "
                        f"${new_total / 100:.2f}"
                    ),
                    remaining_cents=remaining,
                    spent_cents=spent,
                    allocated_cents=allocated,
                )

        return BudgetCheckResult(
            allowed=True,
            warning=None,
            remaining_cents=remaining,
            spent_cents=spent,
            allocated_cents=allocated,
        )

    def compute_spending(
        self,
        company_id: str,
        department_id: str,
        fiscal_year: int,
        config: Optional[CompanyProcurementConfig] = None,
    ) -> int:
        if not config:
            config = self.config_repo.find_by_company_id(
                company_id,
            )
        if not config:
            config = CompanyProcurementConfig.defaults(
                company_id,
            )

        start_month = config.fiscal_year_start_month
        fy_start, fy_end = self._fiscal_year_range(
            fiscal_year, start_month,
        )

        return self.po_repo.sum_totals_by_department_status(
            company_id=company_id,
            department_id=department_id,
            fiscal_year_start=fy_start,
            fiscal_year_end=fy_end,
            statuses=COUNTABLE_STATUSES,
        )

    @staticmethod
    def get_fiscal_year(start_month: int) -> int:
        today = date.today()
        if start_month == 1:
            return today.year
        if today.month >= start_month:
            return today.year
        return today.year - 1

    @staticmethod
    def check_threshold(
        spent_before: int,
        spent_after: int,
        allocated: int,
    ) -> bool:
        if allocated <= 0:
            return False
        threshold = allocated * THRESHOLD_PCT // 100
        return (
            spent_before < threshold
            and spent_after >= threshold
        )

    @staticmethod
    def _fiscal_year_range(
        fiscal_year: int, start_month: int,
    ) -> tuple:
        from datetime import datetime

        fy_start = datetime(fiscal_year, start_month, 1)
        if start_month == 1:
            fy_end = datetime(fiscal_year + 1, 1, 1)
        else:
            fy_end = datetime(
                fiscal_year + 1, start_month, 1,
            )
        return fy_start, fy_end
