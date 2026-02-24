from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetType, SystemLocation
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class SerialNumberExistsError(Exception):
    pass


@dataclass
class CreateAssetCommand(Command):
    company_id: str
    type: str
    brand: str
    model: str
    serial_number: str
    performed_by: str
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    id: Optional[str] = None


class CreateAssetCommandHandler(CommandHandler[CreateAssetCommand]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: CreateAssetCommand) -> None:
        existing = self.asset_repo.find_by_serial_number(command.serial_number, command.company_id)
        if existing:
            raise SerialNumberExistsError(
                f"Asset with serial number '{command.serial_number}' already exists"
            )

        asset_type = AssetType(command.type)

        asset = Asset.create(
            company_id=command.company_id,
            type=asset_type,
            brand=command.brand,
            model=command.model,
            serial_number=command.serial_number,
            purchase_date=command.purchase_date,
            warranty_expiration=command.warranty_expiration,
            notes=command.notes,
            id=command.id,
        )

        # Default location: Almacén Principal
        warehouse = self.asset_repo.find_system_location(
            command.company_id, SystemLocation.MAIN_WAREHOUSE.value,
        )
        if warehouse:
            asset.location_id = warehouse.id

        self.asset_repo.save(asset)

        event = AssetEvent.create(
            asset_id=asset.id,
            event_type="created",
            data={
                "type": asset.type.value,
                "brand": asset.brand,
                "model": asset.model,
                "serial_number": asset.serial_number,
                "status": asset.status.value,
            },
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)
