import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.procurement_bc.purchase_order.application.services.receipt_asset_service import (  # noqa: E501
    ReceiptAssetService,
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


class InvalidReceiveStatusError(Exception):
    pass


class OverReceiveError(Exception):
    pass


class InvalidReceiveQuantityError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


@dataclass
class ReceiveItemInput:
    item_id: str
    received_quantity: int
    create_asset: bool = False
    link_asset_id: Optional[str] = None


@dataclass
class ReceiveItemsCommand(Command):
    purchase_order_id: str
    company_id: str
    items: list[ReceiveItemInput] = field(
        default_factory=list,
    )
    performed_by: str = ""


RECEIVABLE_STATUSES = {
    PurchaseOrderStatus.ORDERED,
    PurchaseOrderStatus.PARTIALLY_RECEIVED,
}


class ReceiveItemsCommandHandler(
    CommandHandler[ReceiveItemsCommand],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
        receipt_asset_service: Optional[
            ReceiptAssetService
        ] = None,
    ):
        self.po_repo = po_repo
        self.receipt_asset_service = receipt_asset_service

    def handle(
        self, command: ReceiveItemsCommand,
    ) -> None:
        po = self.po_repo.find_by_id(
            command.purchase_order_id,
            command.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {command.purchase_order_id} not found"
            )

        if po.status not in RECEIVABLE_STATUSES:
            raise InvalidReceiveStatusError(
                f"Cannot receive items for PO in "
                f"{po.status.value} status"
            )

        item_map = {item.id: item for item in po.items}

        for inp in command.items:
            if inp.received_quantity <= 0:
                raise InvalidReceiveQuantityError(
                    "Received quantity must be > 0"
                )

            po_item = item_map.get(inp.item_id)
            if not po_item:
                raise ItemNotFoundError(
                    f"Item {inp.item_id} not found in PO"
                )

            remaining = (
                po_item.quantity - po_item.received_quantity
            )
            if inp.received_quantity > remaining:
                raise OverReceiveError(
                    f"Cannot receive {inp.received_quantity} "
                    f"for item '{po_item.description}': "
                    f"only {remaining} remaining"
                )

            po_item.received_quantity += (
                inp.received_quantity
            )
            if po_item.received_at is None:
                po_item.received_at = datetime.now(UTC)

            if (
                inp.create_asset
                and po_item.asset_type
                and self.receipt_asset_service
            ):
                asset_id = (
                    self.receipt_asset_service
                    .create_asset_from_item(
                        company_id=command.company_id,
                        po_item=po_item,
                        vendor_name=po.vendor_name,
                        received_by=command.performed_by,
                    )
                )
                po_item.linked_asset_id = asset_id
            elif inp.link_asset_id:
                po_item.linked_asset_id = inp.link_asset_id

        po.receive()
        self.po_repo.save(po)

        logger.info(
            "PO %s received items — status: %s",
            po.po_number,
            po.status.value,
        )
