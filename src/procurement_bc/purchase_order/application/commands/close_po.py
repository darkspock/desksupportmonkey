import logging
from dataclasses import dataclass

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)

logger = logging.getLogger(__name__)


class PONotFoundError(Exception):
    pass


class InvalidCloseStatusError(Exception):
    pass


CLOSABLE_STATUSES = {
    PurchaseOrderStatus.RECEIVED,
    PurchaseOrderStatus.PARTIALLY_RECEIVED,
}


@dataclass
class ClosePurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    performed_by: str = ""


class ClosePurchaseOrderCommandHandler(
    CommandHandler[ClosePurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, command: ClosePurchaseOrderCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        if po.status not in CLOSABLE_STATUSES:
            raise InvalidCloseStatusError(
                f"Cannot close PO in {po.status.value} "
                f"status"
            )

        po.close()
        self.po_repo.save(po)
        logger.info(
            "PO %s closed",
            po.po_number,
        )
