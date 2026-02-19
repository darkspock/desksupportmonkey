from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.procurement_bc.budget.application.services.budget_checker import (  # noqa: E501
    BudgetChecker,
)
from src.procurement_bc.budget.infrastructure.repository import (  # noqa: E501
    CompanyProcurementConfigRepository,
    DepartmentBudgetRepository,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (  # noqa: E501
    PurchaseOrderRepository,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorRepository,
)


def get_po_repo(
    db: Session = Depends(get_db),
) -> PurchaseOrderRepository:
    return PurchaseOrderRepository(db)


def get_vendor_repo(
    db: Session = Depends(get_db),
) -> VendorRepository:
    return VendorRepository(db)


def get_procurement_config_repo(
    db: Session = Depends(get_db),
) -> CompanyProcurementConfigRepository:
    return CompanyProcurementConfigRepository(db)


def get_budget_checker(
    db: Session = Depends(get_db),
) -> BudgetChecker:
    return BudgetChecker(
        budget_repo=DepartmentBudgetRepository(db),
        po_repo=PurchaseOrderRepository(db),
        config_repo=CompanyProcurementConfigRepository(db),
    )
