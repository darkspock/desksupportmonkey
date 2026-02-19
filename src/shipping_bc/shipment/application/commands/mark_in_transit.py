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
class MarkInTransitCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str


class MarkInTransitCommandHandler(
    CommandHandler[MarkInTransitCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, command: MarkInTransitCommand,
    ) -> None:
        shipment = self.shipment_repo.find_by_id(
            command.shipment_id, command.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                "Shipment not found",
            )

        shipment.mark_in_transit()
        self.shipment_repo.save(shipment)
