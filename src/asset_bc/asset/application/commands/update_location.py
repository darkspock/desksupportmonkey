from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.exceptions import (
    LocationNameExistsError,
    LocationNotFoundError,
    SystemLocationError,
)
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class UpdateLocationCommand(Command):
    location_id: str
    company_id: str
    name: Optional[str] = None
    in_use: Optional[bool] = None


class UpdateLocationCommandHandler(CommandHandler[UpdateLocationCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UpdateLocationCommand) -> None:
        location = self.asset_repo.find_location_by_id(command.location_id, command.company_id)
        if not location:
            raise LocationNotFoundError(f"Location '{command.location_id}' not found")

        if location.is_system:
            raise SystemLocationError("Cannot modify system locations")

        if command.name is not None:
            name = command.name.strip()
            if not name:
                raise ValueError("Location name cannot be empty")
            existing = self.asset_repo.find_location_by_name(name, command.company_id)
            if existing and existing.id != location.id:
                raise LocationNameExistsError(f"Location '{name}' already exists")
            location.name = name

        if command.in_use is not None:
            location.in_use = command.in_use

        self.asset_repo.save_location(location)
