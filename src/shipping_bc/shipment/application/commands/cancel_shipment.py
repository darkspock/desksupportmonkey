from dataclasses import dataclass

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
class CancelShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    reason: str


class CancelShipmentCommandHandler(
    CommandHandler[CancelShipmentCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, command: CancelShipmentCommand,
    ) -> None:
        shipment = self.shipment_repo.find_by_id(
            command.shipment_id, command.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                "Shipment not found",
            )

        shipment.cancel(command.reason)
        self.shipment_repo.save(shipment)
