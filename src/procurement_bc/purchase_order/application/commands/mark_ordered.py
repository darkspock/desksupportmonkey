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
class MarkOrderedCommand(Command):
    purchase_order_id: str
    company_id: str
    performed_by: str = ""


class MarkOrderedCommandHandler(
    CommandHandler[MarkOrderedCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, command: MarkOrderedCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        po.mark_ordered()
        self.po_repo.save(po)
        logger.info(
            "PO %s marked as ordered",
            po.po_number,
        )
