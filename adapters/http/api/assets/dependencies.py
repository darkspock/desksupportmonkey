from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_bc.checkout.infrastructure.repository import CheckoutRepository
from src.auth_bc.user.infrastructure.repository import UserRepository


def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


def get_checkout_repo(db: Session = Depends(get_db)) -> CheckoutRepository:
    return CheckoutRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
