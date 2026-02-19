from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.shipment.application.commands.create_shipment import (
    AssetConflictError,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.enums import (
    ShipmentDirection,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class CreateReturnShipmentCommand(Command):
    return_shipment_id: str
    original_shipment_id: str
    company_id: str
    created_by: str
    destination_address_id: str
    asset_ids: list[str]
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class CreateReturnShipmentCommandHandler(
    CommandHandler[CreateReturnShipmentCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self,
        command: CreateReturnShipmentCommand,
    ) -> None:
        original = self.shipment_repo.find_by_id(
            command.original_shipment_id,
            command.company_id,
        )
        if not original:
            raise ShipmentNotFoundError(
                "Original shipment not found",
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

        return_shipment = Shipment.create(
            id=command.return_shipment_id,
            company_id=command.company_id,
            direction=ShipmentDirection.INBOUND,
            destination_type=(
                original.destination_type
            ),
            destination_address_id=(
                command.destination_address_id
            ),
            created_by=command.created_by,
            origin_address_id=(
                original.destination_address_id
            ),
            recipient_name=original.recipient_name,
            recipient_user_id=(
                original.recipient_user_id
            ),
            carrier=command.carrier,
            tracking_number=command.tracking_number,
            return_for_shipment_id=original.id,
            notes=command.notes,
            items=[
                ShipmentItem.create(
                    shipment_id=(
                        command.return_shipment_id
                    ),
                    asset_id=aid,
                )
                for aid in command.asset_ids
            ],
        )

        self.shipment_repo.save(return_shipment)
