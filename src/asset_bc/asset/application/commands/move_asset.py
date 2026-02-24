from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.exceptions import LocationNotFoundError
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


class AssetDecommissionedError(Exception):
    pass


@dataclass
class MoveAssetCommand(Command):
    asset_id: str
    company_id: str
    location_id: str
    performed_by: str
    notes: Optional[str] = None


class MoveAssetCommandHandler(CommandHandler[MoveAssetCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: MoveAssetCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        if asset.status == AssetStatus.DECOMMISSIONED:
            raise AssetDecommissionedError("Cannot move a decommissioned asset")

        location = self.asset_repo.find_location_by_id(command.location_id, command.company_id)
        if not location:
            raise LocationNotFoundError(f"Location '{command.location_id}' not found")

        changes = asset.move_to(command.location_id)
        if not changes:
            return  # No-op: already at this location

        self.asset_repo.save(asset)

        old_loc = None
        if changes.get("old_location_id"):
            old_loc = self.asset_repo.find_location_by_id(changes["old_location_id"], command.company_id)

        event_data = {
            "old_location_id": changes.get("old_location_id"),
            "old_location_name": old_loc.name if old_loc else None,
            "new_location_id": command.location_id,
            "new_location_name": location.name,
        }
        if command.notes:
            event_data["notes"] = command.notes

        event = AssetEvent.create(
            asset_id=asset.id,
            event_type="location_changed",
            data=event_data,
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)
