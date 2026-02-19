from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import (
    get_current_user,
    require_role,
)
from adapters.http.api.maintenance.controllers import (
    MaintenanceController,
)
from adapters.http.api.maintenance.dependencies import (
    get_maintenance_controller,
)
from adapters.http.api.maintenance.schemas import (
    AssignMaintenanceRequest,
    CancelMaintenanceRequest,
    CompleteMaintenanceRequest,
    CreateMaintenanceRecordRequest,
    SkipMaintenanceRequest,
    UpdateMaintenanceRecordRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.maintenance_bc.maintenance_record.application.commands.assign_maintenance_record import (
    MaintenanceRecordNotFoundError as AssignNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.cancel_maintenance import (
    MaintenanceRecordNotFoundError as CancelNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.complete_maintenance import (
    MaintenanceRecordNotFoundError as CompleteNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.assign_maintenance_record import (
    TechnicianNotFoundError as AssignTechnicianNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.create_maintenance_record import (
    AssetNotFoundError,
    TechnicianNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.skip_maintenance import (
    MaintenanceRecordNotFoundError as SkipNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.start_maintenance import (
    MaintenanceRecordNotFoundError as StartNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.commands.update_maintenance_record import (
    MaintenanceRecordNotFoundError as UpdateNotFoundError,
)
from src.maintenance_bc.maintenance_record.application.queries.get_maintenance_record import (
    MaintenanceRecordNotFoundError as GetNotFoundError,
)
from src.maintenance_bc.maintenance_record.domain.enums import (
    InvalidMaintenanceStatusTransitionError,
)

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])
tech_dep = require_role(UserRole.TECHNICIAN)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    body: CreateMaintenanceRecordRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.create(
            company_id=current_user.company_id,
            actor_id=current_user.id,
            asset_id=body.asset_id,
            title=body.title,
            priority=body.priority,
            description=body.description,
            technician_id=body.technician_id,
            template_id=body.template_id,
            plan_id=body.plan_id,
            checklist_items=body.checklist_items,
            scheduled_at=body.scheduled_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (AssetNotFoundError, TechnicianNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
def list_maintenance_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    maintenance_status: Optional[str] = Query(None, alias="status"),
    asset_id: Optional[str] = Query(None),
    technician_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    scheduled_from: Optional[datetime] = Query(None),
    scheduled_to: Optional[datetime] = Query(None),
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    records, total = controller.list(
        company_id=current_user.company_id,
        page=page,
        page_size=page_size,
        status=maintenance_status,
        asset_id=asset_id,
        technician_id=technician_id,
        priority=priority,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
    )
    return {
        "data": records,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{record_id}")
def get_maintenance_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.get(
            company_id=current_user.company_id,
            record_id=record_id,
        )
    except GetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{record_id}")
def update_maintenance_record(
    record_id: str,
    body: UpdateMaintenanceRecordRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.update(
            company_id=current_user.company_id,
            record_id=record_id,
            title=body.title,
            description=body.description,
            priority=body.priority,
            checklist_items=body.checklist_items,
            scheduled_at=body.scheduled_at,
        )
    except UpdateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{record_id}/assign")
def assign_maintenance_record(
    record_id: str,
    body: AssignMaintenanceRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.assign(
            company_id=current_user.company_id,
            record_id=record_id,
            technician_id=body.technician_id,
        )
    except (AssignNotFoundError, AssignTechnicianNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{record_id}/start")
def start_maintenance(
    record_id: str,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.start(
            company_id=current_user.company_id,
            record_id=record_id,
        )
    except StartNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, InvalidMaintenanceStatusTransitionError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{record_id}/complete")
def complete_maintenance(
    record_id: str,
    body: CompleteMaintenanceRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.complete(
            company_id=current_user.company_id,
            actor_id=current_user.id,
            record_id=record_id,
            completion_notes=body.completion_notes,
            actual_findings=body.actual_findings,
        )
    except CompleteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidMaintenanceStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{record_id}/cancel")
def cancel_maintenance(
    record_id: str,
    body: CancelMaintenanceRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.cancel(
            company_id=current_user.company_id,
            actor_id=current_user.id,
            record_id=record_id,
            reason=body.reason,
        )
    except CancelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, InvalidMaintenanceStatusTransitionError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/{record_id}/skip")
def skip_maintenance(
    record_id: str,
    body: SkipMaintenanceRequest,
    current_user: User = Depends(tech_dep),
    controller: MaintenanceController = Depends(get_maintenance_controller),
):
    try:
        return controller.skip(
            company_id=current_user.company_id,
            record_id=record_id,
            reason=body.reason,
        )
    except SkipNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, InvalidMaintenanceStatusTransitionError) as e:
        raise HTTPException(status_code=422, detail=str(e))
