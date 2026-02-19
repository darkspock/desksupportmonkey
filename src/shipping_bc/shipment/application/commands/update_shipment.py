from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class UpdateShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    notes: Optional[str] = None


class UpdateShipmentCommandHandler(
    CommandHandler[UpdateShipmentCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, command: UpdateShipmentCommand,
    ) -> None:
        shipment = self.shipment_repo.find_by_id(
            command.shipment_id, command.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                "Shipment not found",
            )

        if command.carrier is not None:
            shipment.carrier = command.carrier
        if command.tracking_number is not None:
            shipment.tracking_number = (
                command.tracking_number
            )
        if command.tracking_url is not None:
            shipment.tracking_url = command.tracking_url
        if command.notes is not None:
            shipment.notes = command.notes

        self.shipment_repo.save(shipment)
