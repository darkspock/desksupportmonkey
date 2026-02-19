from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.company_bc.assignment_config.infrastructure.repository import (  # noqa: E501
    AssignmentConfigRepository,
)


def get_config_repo(
    db: Session = Depends(get_db),
) -> AssignmentConfigRepository:
    return AssignmentConfigRepository(db)
