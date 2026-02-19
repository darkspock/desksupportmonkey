import logging
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.procurement_bc.budget.application.services.budget_checker import (
        BudgetChecker,
    )


class PONotFoundError(Exception):
    pass


class BudgetExceededException(Exception):
    def __init__(self, message: str, shortfall_cents: int):
        self.shortfall_cents = shortfall_cents
        super().__init__(message)


@dataclass
class ApproveResult:
    budget_warning: Optional[str] = None
    threshold_crossed: bool = False
    department_id: Optional[str] = None
    spent_cents: int = 0
    allocated_cents: int = 0


@dataclass
class ApprovePurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    approved_by: str = ""


class ApprovePurchaseOrderCommandHandler(
    CommandHandler[ApprovePurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
        budget_checker: Optional[
            "BudgetChecker"
        ] = None,
    ):
        self.po_repo = po_repo
        self.budget_checker = budget_checker
        self._last_result: Optional[ApproveResult] = None

    def handle(
        self, command: ApprovePurchaseOrderCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        result = ApproveResult(department_id=po.department_id)

        if self.budget_checker:
            check = self.budget_checker.check_approval(
                command.company_id,
                po.department_id,
                po.total_amount_cents,
            )

            if not check.allowed:
                shortfall = (
                    check.spent_cents
                    + po.total_amount_cents
                    - check.allocated_cents
                )
                raise BudgetExceededException(
                    check.warning or "Budget exceeded",
                    shortfall_cents=shortfall,
                )

            if check.warning:
                result.budget_warning = check.warning

            spent_before = check.spent_cents
            spent_after = (
                spent_before + po.total_amount_cents
            )
            if (
                check.allocated_cents > 0
                and self.budget_checker.check_threshold(
                    spent_before,
                    spent_after,
                    check.allocated_cents,
                )
            ):
                result.threshold_crossed = True
                result.spent_cents = spent_after
                result.allocated_cents = (
                    check.allocated_cents
                )

        po.approve(command.approved_by)
        self.po_repo.save(po)
        logger.info(
            "PO %s approved by %s",
            po.po_number,
            command.approved_by,
        )
        self._last_result = result

    @property
    def last_result(self) -> ApproveResult:
        if self._last_result is None:
            raise RuntimeError(
                "No approval result available yet",
            )
        return self._last_result
