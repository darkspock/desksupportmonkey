import logging
from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)
from src.procurement_bc.budget.domain.repository import (
    CompanyProcurementConfigRepositoryInterface,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)


class PONotFoundError(Exception):
    pass


@dataclass
class SubmitPurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    performed_by: str = ""


class SubmitResult:
    def __init__(
        self,
        auto_approved: bool = False,
    ):
        self.auto_approved = auto_approved


class SubmitPurchaseOrderCommandHandler(
    CommandHandler[SubmitPurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        self.po_repo = po_repo
        self.config_repo = config_repo
        self._last_result: Optional[SubmitResult] = None

    def handle(
        self, command: SubmitPurchaseOrderCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        po.submit()

        config = self.config_repo.find_by_company_id(
            command.company_id,
        )
        if not config:
            config = CompanyProcurementConfig.defaults(
                command.company_id,
            )

        auto_approved = False
        threshold = config.approval_threshold_cents
        if (
            threshold > 0
            and po.total_amount_cents <= threshold
        ):
            po.approve(command.performed_by)
            auto_approved = True
            logger.info(
                "PO %s auto-approved (total %d <= threshold %d)",
                po.po_number,
                po.total_amount_cents,
                threshold,
            )

        self.po_repo.save(po)

        if not auto_approved:
            logger.info(
                "PO %s submitted for approval",
                po.po_number,
            )

        self._last_result = SubmitResult(
            auto_approved=auto_approved,
        )

    @property
    def last_result(self) -> SubmitResult:
        if self._last_result is None:
            raise RuntimeError(
                "No submit result available yet",
            )
        return self._last_result
