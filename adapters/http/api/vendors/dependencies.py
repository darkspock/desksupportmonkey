from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorRepository,
)


def get_vendor_repo(
    db: Session = Depends(get_db),
) -> VendorRepository:
    return VendorRepository(db)
