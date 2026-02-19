from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.procurement_bc.budget.application.services.budget_checker import (
    BudgetChecker,
)
from src.procurement_bc.budget.infrastructure.repository import (
    CompanyProcurementConfigRepository,
    DepartmentBudgetRepository,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (
    PurchaseOrderRepository,
)
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.shipping_bc.shipment.infrastructure.repository import ShipmentRepository
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)


def get_request_repo(db: Session = Depends(get_db)) -> RequestRepository:
    return RequestRepository(db)


def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


def get_budget_repo(db: Session = Depends(get_db)) -> DepartmentBudgetRepository:
    return DepartmentBudgetRepository(db)


def get_po_repo(db: Session = Depends(get_db)) -> PurchaseOrderRepository:
    return PurchaseOrderRepository(db)


def get_budget_checker(db: Session = Depends(get_db)) -> BudgetChecker:
    budget_repo = DepartmentBudgetRepository(db)
    config_repo = CompanyProcurementConfigRepository(db)
    po_repo = PurchaseOrderRepository(db)
    return BudgetChecker(budget_repo=budget_repo, po_repo=po_repo, config_repo=config_repo)


def get_shipment_repo(db: Session = Depends(get_db)) -> ShipmentRepository:
    return ShipmentRepository(db)


def get_maintenance_record_repo(
    db: Session = Depends(get_db),
) -> MaintenanceRecordRepository:
    return MaintenanceRecordRepository(db)
