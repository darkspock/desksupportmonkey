from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.appointment_bc.appointment.infrastructure.repository import AppointmentRepository
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.notification_bc.notification.infrastructure.repository import NotificationRepository
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.shipping_bc.shipment.infrastructure.repository import ShipmentRepository
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)


def get_asset_repo(db: Session = Depends(get_db)) -> AssetRepository:
    return AssetRepository(db)


def get_request_repo(db: Session = Depends(get_db)) -> RequestRepository:
    return RequestRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_notification_repo(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


def get_appointment_repo(db: Session = Depends(get_db)) -> AppointmentRepository:
    return AppointmentRepository(db)


def get_shipment_repo(db: Session = Depends(get_db)) -> ShipmentRepository:
    return ShipmentRepository(db)


def get_maintenance_record_repo(
    db: Session = Depends(get_db),
) -> MaintenanceRecordRepository:
    return MaintenanceRecordRepository(db)
