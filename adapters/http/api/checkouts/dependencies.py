from fastapi import Depends
from sqlalchemy.orm import Session

from adapters.http.api.checkouts.adapters import MaintenanceRecordCreatorAdapter
from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_bc.checkout.application.ports import MaintenanceRecordCreator
from src.asset_bc.checkout.infrastructure.repository import CheckoutRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.maintenance_bc.maintenance_record.infrastructure.asset_lookup import (
    AssetRepositoryLookupAdapter,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)


def get_checkout_repo(db: Session = Depends(get_db)) -> CheckoutRepository:
    return CheckoutRepository(db)


def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_maintenance_creator(db: Session = Depends(get_db)) -> MaintenanceRecordCreator:
    asset_repo = AssetRepository(db)
    return MaintenanceRecordCreatorAdapter(
        record_repo=MaintenanceRecordRepository(db),
        asset_lookup=AssetRepositoryLookupAdapter(asset_repo),
        user_lookup=UserRepository(db),  # type: ignore[arg-type]
    )
