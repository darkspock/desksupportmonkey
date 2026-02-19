from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.shipment.application.services.delivery_asset_service import (
    DeliveryAssetService,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class DeliverShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    notes: Optional[str] = None


class DeliverShipmentCommandHandler(
    CommandHandler[DeliverShipmentCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
        delivery_asset_service: DeliveryAssetService,
    ):
        self.shipment_repo = shipment_repo
        self.delivery_asset_service = (
            delivery_asset_service
        )

    def handle(
        self, command: DeliverShipmentCommand,
    ) -> None:
        shipment = self.shipment_repo.find_by_id(
            command.shipment_id, command.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                "Shipment not found",
            )

        shipment.deliver()

        if command.notes is not None:
            shipment.notes = command.notes

        self.shipment_repo.save(shipment)

        self.delivery_asset_service \
            .update_assets_on_delivery(shipment)
