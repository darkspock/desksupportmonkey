from fastapi import Depends
from sqlalchemy.orm import Session

from adapters.http.api.maintenance_templates.controllers import (
    MaintenanceTemplatesController,
)
from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
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
from src.maintenance_bc.maintenance_template.infrastructure.repository import (
    MaintenancePlanRepository,
    MaintenanceTemplateRepository,
)


def get_template_repo(
    db: Session = Depends(get_db),
) -> MaintenanceTemplateRepository:
    return MaintenanceTemplateRepository(db)


def get_plan_repo(
    db: Session = Depends(get_db),
) -> MaintenancePlanRepository:
    return MaintenancePlanRepository(db)


def get_record_repo(
    db: Session = Depends(get_db),
) -> MaintenanceRecordRepository:
    return MaintenanceRecordRepository(db)


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetLookup:
    return AssetRepositoryLookupAdapter(
        AssetRepository(db),
    )


def get_maintenance_templates_controller(
    db: Session = Depends(get_db),
) -> MaintenanceTemplatesController:
    return MaintenanceTemplatesController(
        template_repo=MaintenanceTemplateRepository(db),
        plan_repo=MaintenancePlanRepository(db),
        record_repo=MaintenanceRecordRepository(db),
        asset_lookup=AssetRepositoryLookupAdapter(AssetRepository(db)),
    )
