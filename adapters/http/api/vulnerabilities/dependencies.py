from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.vulnerability_bc.vulnerability.infrastructure.repository import (
    VulnerabilityRepository,
)
from src.vulnerability_bc.vulnerability.infrastructure.vuln_asset_repository import (
    VulnerabilityAssetRepository,
)


def get_vulnerability_repo(
    db: Session = Depends(get_db),
) -> VulnerabilityRepository:
    return VulnerabilityRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_vuln_asset_repo(
    db: Session = Depends(get_db),
) -> VulnerabilityAssetRepository:
    return VulnerabilityAssetRepository(db)


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetRepository:
    return AssetRepository(db)


def get_request_repo(
    db: Session = Depends(get_db),
) -> RequestRepository:
    return RequestRepository(db)
