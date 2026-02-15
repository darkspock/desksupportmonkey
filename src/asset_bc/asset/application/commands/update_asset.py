from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


class AssetNotFoundError(Exception):
    pass


@dataclass
class UpdateAssetCommand:
    asset_id: str
    company_id: str
    performed_by: str
    brand: Optional[str] = None
    model: Optional[str] = None
    notes: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None


class UpdateAssetCommandHandler:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, command: UpdateAssetCommand) -> Asset:
        asset = self.asset_repo.find_by_id(command.asset_id, command.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{command.asset_id}' not found")

        changes = asset.update(
            brand=command.brand,
            model=command.model,
            notes=command.notes,
            purchase_date=command.purchase_date,
            warranty_expiration=command.warranty_expiration,
        )

        asset = self.asset_repo.save(asset)

        if changes:
            event = AssetEvent.create(
                asset_id=asset.id,
                event_type="updated",
                data=changes,
                performed_by=command.performed_by,
            )
            self.asset_repo.save_event(event)

        return asset
