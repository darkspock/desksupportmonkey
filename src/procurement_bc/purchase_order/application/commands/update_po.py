import logging
from dataclasses import dataclass, field
from typing import Optional

import ulid

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.purchase_order.application.commands.create_po import (  # noqa: E501
    POItemInput,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrderItem,
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


class PONotDraftError(Exception):
    pass


@dataclass
class UpdatePurchaseOrderCommand(Command):
    purchase_order_id: str
    company_id: str
    vendor_name: str
    department_id: str
    items: list[POItemInput] = field(
        default_factory=list,
    )
    request_ids: list[str] = field(
        default_factory=list,
    )
    vendor_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by: str = ""


class UpdatePurchaseOrderCommandHandler(
    CommandHandler[UpdatePurchaseOrderCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, command: UpdatePurchaseOrderCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )
        if po.status != PurchaseOrderStatus.DRAFT:
            raise PONotDraftError(
                "Only DRAFT purchase orders can be edited"
            )

        po.vendor_id = command.vendor_id
        po.vendor_name = command.vendor_name
        po.department_id = command.department_id
        po.notes = command.notes
        po.request_ids = list(command.request_ids)

        po.items = []
        for item_input in command.items:
            total = (
                item_input.quantity * item_input.unit_cost_cents
            )
            po.items.append(
                PurchaseOrderItem(
                    id=str(ulid.new()),
                    purchase_order_id=po.id,
                    description=item_input.description,
                    quantity=item_input.quantity,
                    unit_cost_cents=item_input.unit_cost_cents,
                    total_cost_cents=total,
                    asset_type=item_input.asset_type,
                    notes=item_input.notes,
                )
            )

        po.recalculate_total()
        self.po_repo.save(po)
        logger.info("PO %s updated", po.po_number)
