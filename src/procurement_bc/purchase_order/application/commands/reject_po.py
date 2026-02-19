import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)


class PONotFoundError(Exception):
    pass


@dataclass
class RejectPurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    reason: str
    performed_by: str = ""


class RejectPurchaseOrderCommandHandler(
    CommandHandler[RejectPurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, command: RejectPurchaseOrderCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        po.reject(command.reason)
        self.po_repo.save(po)
        logger.info(
            "PO %s rejected: %s",
            po.po_number,
            command.reason,
        )
