from fastapi import Depends
from sqlalchemy.orm import Session

from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.maintenance.controllers import (
    MaintenanceController,
)
from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.auth_bc.user.infrastructure.repository import (
    UserRepository,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)
from src.maintenance_bc.maintenance_record.infrastructure.asset_lookup import (
    AssetRepositoryLookupAdapter,
)
from src.notification_bc.notification.application.services.event_bus import (
    EventBus,
)


def get_maintenance_record_repo(
    db: Session = Depends(get_db),
) -> MaintenanceRecordRepository:
    return MaintenanceRecordRepository(db)


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetLookup:
    return AssetRepositoryLookupAdapter(
        AssetRepository(db),
    )


def get_maintenance_controller(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> MaintenanceController:
    return MaintenanceController(
        record_repo=MaintenanceRecordRepository(db),
        asset_lookup=AssetRepositoryLookupAdapter(AssetRepository(db)),
        user_lookup=UserRepository(db),
        event_bus=event_bus,
        db=db,
    )
