from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


class AssetConflictError(Exception):
    pass


@dataclass
class CreateShipmentCommand(Command):
    shipment_id: str
    company_id: str
    direction: str
    destination_type: str
    destination_location_id: str
    created_by: str
    asset_ids: list[str]
    origin_location_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_user_id: Optional[str] = None
    carrier: Optional[str] = None
    service_level: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    items_description: Optional[str] = None
    internal_notes: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
    return_for_shipment_id: Optional[str] = None
    notes: Optional[str] = None


class CreateShipmentCommandHandler(
    CommandHandler[CreateShipmentCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, command: CreateShipmentCommand,
    ) -> None:
        direction = ShipmentDirection(command.direction)
        destination_type = DestinationType(
            command.destination_type,
        )

        for asset_id in command.asset_ids:
            active = (
                self.shipment_repo
                .find_active_by_asset_id(
                    asset_id, command.company_id,
                )
            )
            if active:
                raise AssetConflictError(
                    f"Asset {asset_id} is already in "
                    f"an active shipment",
                )

        shipment = Shipment.create(
            id=command.shipment_id,
            company_id=command.company_id,
            direction=direction,
            destination_type=destination_type,
            destination_location_id=(
                command.destination_location_id
            ),
            created_by=command.created_by,
            origin_location_id=command.origin_location_id,
            recipient_name=command.recipient_name,
            recipient_user_id=(
                command.recipient_user_id
            ),
            carrier=command.carrier,
            service_level=command.service_level,
            tracking_number=command.tracking_number,
            tracking_url=command.tracking_url,
            items_description=(
                command.items_description
            ),
            internal_notes=command.internal_notes,
            request_id=command.request_id,
            po_id=command.po_id,
            return_for_shipment_id=(
                command.return_for_shipment_id
            ),
            notes=command.notes,
            items=[
                ShipmentItem.create(
                    shipment_id=command.shipment_id,
                    asset_id=aid,
                )
                for aid in command.asset_ids
            ],
        )

        self.shipment_repo.save(shipment)
