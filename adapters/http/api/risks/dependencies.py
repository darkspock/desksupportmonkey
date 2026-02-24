from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.risk_bc.risk.infrastructure.repository import RiskRepository


def get_risk_repo(
    db: Session = Depends(get_db),
) -> RiskRepository:
    return RiskRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)
