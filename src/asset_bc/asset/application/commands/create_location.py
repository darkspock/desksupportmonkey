from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import AssetLocation
from src.asset_bc.asset.domain.exceptions import LocationNameExistsError
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class CreateLocationCommand(Command):
    company_id: str
    name: str
    in_use: bool = True
    id: Optional[str] = None


class CreateLocationCommandHandler(CommandHandler[CreateLocationCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: CreateLocationCommand) -> None:
        existing = self.asset_repo.find_location_by_name(command.name, command.company_id)
        if existing:
            raise LocationNameExistsError(
                f"Location '{command.name}' already exists"
            )

        location = AssetLocation.create(
            company_id=command.company_id,
            name=command.name,
            in_use=command.in_use,
            id=command.id,
        )
        self.asset_repo.save_location(location)
