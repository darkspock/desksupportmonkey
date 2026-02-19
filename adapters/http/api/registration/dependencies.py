from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_magic_link_repo(db: Session = Depends(get_db)) -> MagicLinkRepository:
    return MagicLinkRepository(db)
