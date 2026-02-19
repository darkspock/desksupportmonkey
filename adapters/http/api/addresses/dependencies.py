from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.shipping_bc.address.infrastructure.repository import (
    ShippingAddressRepository,
)


def get_address_repo(
    db: Session = Depends(get_db),
) -> ShippingAddressRepository:
    return ShippingAddressRepository(db)
