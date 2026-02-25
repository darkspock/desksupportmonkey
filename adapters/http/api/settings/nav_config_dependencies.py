from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.company_bc.nav_config.infrastructure.repository import (
    NavConfigRepository,
)


def get_nav_config_repo(
    db: Session = Depends(get_db),
) -> NavConfigRepository:
    return NavConfigRepository(db)
