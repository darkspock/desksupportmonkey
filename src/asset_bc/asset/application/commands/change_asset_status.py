from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class ChangeAssetStatusCommand(Command):
    asset_id: str
    company_id: str
    new_status: str
    performed_by: str


class ChangeAssetStatusCommandHandler(CommandHandler[ChangeAssetStatusCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: ChangeAssetStatusCommand) -> None:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        old_status = asset.status
        new_status = AssetStatus(command.new_status)
        was_assigned = asset.assigned_to is not None
        old_location_id = asset.location_id

        asset.change_status(new_status)
        self.asset_repo.save(asset)

        event = AssetEvent.create(
            asset_id=asset.id,
            event_type="status_changed",
            data={"old_status": old_status.value, "new_status": new_status.value},
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)

        if new_status == AssetStatus.DECOMMISSIONED and was_assigned:
            unassign_event = AssetEvent.create(
                asset_id=asset.id,
                event_type="unassigned",
                data={"reason": "decommissioned"},
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(unassign_event)

        # Emit location_changed event if location was cleared on decommission
        if new_status == AssetStatus.DECOMMISSIONED and old_location_id:
            old_loc = self.asset_repo.find_location_by_id(old_location_id, command.company_id)
            loc_event = AssetEvent.create(
                asset_id=asset.id,
                event_type="location_changed",
                data={
                    "old_location_id": old_location_id,
                    "old_location_name": old_loc.name if old_loc else None,
                    "new_location_id": None,
                    "new_location_name": None,
                    "reason": "decommissioned",
                },
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(loc_event)
