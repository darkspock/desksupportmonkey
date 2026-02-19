from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.procurement_bc.budget.infrastructure.repository import (  # noqa: E501
    CompanyProcurementConfigRepository,
)


def get_procurement_config_repo(
    db: Session = Depends(get_db),
) -> CompanyProcurementConfigRepository:
    return CompanyProcurementConfigRepository(db)
