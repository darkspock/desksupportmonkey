from fastapi import Depends
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.stripe_client import StripeClient
from src.company_bc.company.infrastructure.repository import CompanyRepository


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_stripe_client() -> StripeClient:
    return StripeClient(
        secret_key=settings.stripe.SECRET_KEY,
        open_source_mode=settings.stripe.OPEN_SOURCE_MODE,
    )
