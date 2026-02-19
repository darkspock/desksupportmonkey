from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.shipping_bc.shipment.application.services.delivery_asset_service import (
    DeliveryAssetService,
)
from src.shipping_bc.shipment.infrastructure.repository import (
    ShipmentRepository,
)


def get_shipment_repo(
    db: Session = Depends(get_db),
) -> ShipmentRepository:
    return ShipmentRepository(db)


def get_delivery_asset_service(
    db: Session = Depends(get_db),
) -> DeliveryAssetService:
    return DeliveryAssetService(AssetRepository(db))
