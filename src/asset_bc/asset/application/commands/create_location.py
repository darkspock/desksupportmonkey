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
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_personal: bool = False
    user_id: Optional[str] = None


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
            street_line_1=command.street_line_1,
            street_line_2=command.street_line_2,
            city=command.city,
            state=command.state,
            postal_code=command.postal_code,
            country=command.country,
            phone=command.phone,
            is_personal=command.is_personal,
            user_id=command.user_id,
        )
        self.asset_repo.save_location(location)
