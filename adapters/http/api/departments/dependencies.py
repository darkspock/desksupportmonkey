from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.user.infrastructure.repository import (
    UserRepository,
)
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (
    PurchaseOrderRepository,
)


def get_department_repo(db: Session = Depends(get_db)) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_po_repo(db: Session = Depends(get_db)) -> PurchaseOrderRepository:
    return PurchaseOrderRepository(db)
