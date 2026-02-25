from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.exceptions import (
    LocationNameExistsError,
    LocationNotFoundError,
    SystemLocationError,
)
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


_UNSET = object()


@dataclass
class UpdateLocationCommand(Command):
    location_id: str
    company_id: str
    name: Optional[str] = None
    in_use: Optional[bool] = None
    street_line_1: object = _UNSET
    street_line_2: object = _UNSET
    city: object = _UNSET
    state: object = _UNSET
    postal_code: object = _UNSET
    country: object = _UNSET
    phone: object = _UNSET


class UpdateLocationCommandHandler(CommandHandler[UpdateLocationCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UpdateLocationCommand) -> None:
        location = self.asset_repo.find_location_by_id(command.location_id, command.company_id)
        if not location:
            raise LocationNotFoundError(f"Location '{command.location_id}' not found")

        if not location.is_system:
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

        if command.street_line_1 is not _UNSET:
            location.street_line_1 = command.street_line_1  # type: ignore[assignment]
        if command.street_line_2 is not _UNSET:
            location.street_line_2 = command.street_line_2  # type: ignore[assignment]
        if command.city is not _UNSET:
            location.city = command.city  # type: ignore[assignment]
        if command.state is not _UNSET:
            location.state = command.state  # type: ignore[assignment]
        if command.postal_code is not _UNSET:
            location.postal_code = command.postal_code  # type: ignore[assignment]
        if command.country is not _UNSET:
            location.country = command.country  # type: ignore[assignment]
        if command.phone is not _UNSET:
            location.phone = command.phone  # type: ignore[assignment]

        self.asset_repo.save_location(location)
