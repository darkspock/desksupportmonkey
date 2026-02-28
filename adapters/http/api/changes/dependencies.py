from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.change_bc.change_request.infrastructure.repository import (
    ChangeRequestRepository,
)


def get_change_repo(
    db: Session = Depends(get_db),
) -> ChangeRequestRepository:
    return ChangeRequestRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetRepository:
    return AssetRepository(db)
