from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.company_bc.classification_config.infrastructure.repository import (
    ClassificationConfigRepository,
)


def get_classification_config_repo(
    db: Session = Depends(get_db),
) -> ClassificationConfigRepository:
    return ClassificationConfigRepository(db)
