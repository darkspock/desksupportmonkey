from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorDependencyRepository,
)


def get_dependency_repo(
    db: Session = Depends(get_db),
) -> VendorDependencyRepository:
    return VendorDependencyRepository(db)
