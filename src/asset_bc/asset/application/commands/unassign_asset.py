from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset, AssetEvent, InvalidAssignmentError
from src.asset_bc.asset.domain.enums import SystemLocation
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class UnassignAssetCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str


class UnassignAssetCommandHandler(CommandHandler[UnassignAssetCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UnassignAssetCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        previous_user_id = asset.assigned_to
        old_location_id = asset.location_id
        asset.unassign()

        # Auto-move to "Almacén Principal" location
        warehouse = self.asset_repo.find_system_location(
            command.company_id, SystemLocation.MAIN_WAREHOUSE.value,
        )
        if warehouse:
            asset.location_id = warehouse.id

        self.asset_repo.save(asset)

        event = AssetEvent.create(
            asset_id=asset.id,
            event_type="unassigned",
            data={
                "previous_user_id": previous_user_id,
                "unassigned_by": command.performed_by,
            },
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)

        # Emit location_changed event if location actually changed
        if warehouse and old_location_id != warehouse.id:
            old_loc = None
            if old_location_id:
                old_loc = self.asset_repo.find_location_by_id(old_location_id, command.company_id)
            loc_event = AssetEvent.create(
                asset_id=asset.id,
                event_type="location_changed",
                data={
                    "old_location_id": old_location_id,
                    "old_location_name": old_loc.name if old_loc else None,
                    "new_location_id": warehouse.id,
                    "new_location_name": warehouse.name,
                    "reason": "unassigned",
                },
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(loc_event)
