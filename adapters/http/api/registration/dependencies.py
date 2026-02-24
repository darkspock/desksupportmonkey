from fastapi import Depends
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.stripe_client import StripeClient
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_type_bc.definition.infrastructure.repository import (
    AssetTypeDefinitionRepository,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_magic_link_repo(db: Session = Depends(get_db)) -> MagicLinkRepository:
    return MagicLinkRepository(db)


def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


def get_asset_type_repo(db: Session = Depends(get_db)) -> AssetTypeDefinitionRepository:
    return AssetTypeDefinitionRepository(db)


def get_stripe_client() -> StripeClient:
    return StripeClient(
        secret_key=settings.stripe.STRIPE_SECRET_KEY,
        open_source_mode=settings.stripe.OPEN_SOURCE_MODE,
    )
