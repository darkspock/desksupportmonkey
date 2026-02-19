from dataclasses import dataclass, field

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.shipping_bc.shipment.application.commands.create_shipment import (
    AssetConflictError,
)
from src.shipping_bc.shipment.domain.entities import (
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class ModifyShipmentItemsCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    add_asset_ids: list[str] = field(
        default_factory=list,
    )
    remove_item_ids: list[str] = field(
        default_factory=list,
    )


class ModifyShipmentItemsCommandHandler(
    CommandHandler[ModifyShipmentItemsCommand],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self,
        command: ModifyShipmentItemsCommand,
    ) -> None:
        shipment = self.shipment_repo.find_by_id(
            command.shipment_id, command.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                "Shipment not found",
            )

        for item_id in command.remove_item_ids:
            shipment.remove_item(item_id)

        for asset_id in command.add_asset_ids:
            active = (
                self.shipment_repo
                .find_active_by_asset_id(
                    asset_id, command.company_id,
                )
            )
            conflict = [
                s for s in active
                if s.id != shipment.id
            ]
            if conflict:
                raise AssetConflictError(
                    f"Asset {asset_id} is already in "
                    f"an active shipment",
                )
            item = ShipmentItem.create(
                shipment_id=shipment.id,
                asset_id=asset_id,
            )
            shipment.add_item(item)

        self.shipment_repo.save(shipment)
