from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset, AssetEvent, InvalidAssignmentError
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


class AssetNotFoundError(Exception):
    pass


@dataclass
class UnassignAssetCommand:
    asset_id: str
    company_id: str
    performed_by: str


class UnassignAssetCommandHandler:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UnassignAssetCommand) -> Asset:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        previous_user_id = asset.assigned_to
        asset.unassign()
        asset = self.asset_repo.save(asset)

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

        return asset
