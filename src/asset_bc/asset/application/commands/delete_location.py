from dataclasses import dataclass

from src.asset_bc.asset.domain.exceptions import (
    LocationHasAssetsError,
    LocationNotFoundError,
    SystemLocationError,
)
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class DeleteLocationCommand(Command):
    location_id: str
    company_id: str


class DeleteLocationCommandHandler(CommandHandler[DeleteLocationCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: DeleteLocationCommand) -> None:
        location = self.asset_repo.find_location_by_id(command.location_id, command.company_id)
        if not location:
            raise LocationNotFoundError(f"Location '{command.location_id}' not found")

        if location.is_system:
            raise SystemLocationError("Cannot delete system locations")

        asset_count = self.asset_repo.count_assets_at_location(command.location_id)
        if asset_count > 0:
            raise LocationHasAssetsError(
                f"Cannot delete location with {asset_count} asset(s). Move assets first."
            )

        self.asset_repo.delete_location(command.location_id)
