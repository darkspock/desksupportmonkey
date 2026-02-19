from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.maintenance_templates.controllers import (
    MaintenanceTemplatesController,
)
from adapters.http.api.maintenance_templates.dependencies import (
    get_maintenance_templates_controller,
)
from adapters.http.api.maintenance_templates.schemas import (
    ApplyTemplateRequest,
    CreateMaintenanceTemplateRequest,
    UpdateMaintenanceTemplateRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.maintenance_bc.maintenance_template.application.commands.apply_template_to_assets import (
    MaintenanceTemplateNotFoundError as ApplyTemplateNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.commands.deactivate_plan import (
    MaintenancePlanNotFoundError as DeactivatePlanNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.commands.delete_maintenance_template import (
    MaintenanceTemplateNotFoundError as DeleteTemplateNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.commands.update_maintenance_template import (
    MaintenanceTemplateNotFoundError as UpdateTemplateNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_plan import (
    MaintenancePlanNotFoundError as GetPlanNotFoundError,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_template import (
    MaintenanceTemplateNotFoundError as GetTemplateNotFoundError,
)

router = APIRouter(tags=["maintenance-templates"])
admin_dep = require_role(UserRole.ADMIN)


@router.post("/api/v1/maintenance-templates", status_code=status.HTTP_201_CREATED)
def create_maintenance_template(
    body: CreateMaintenanceTemplateRequest,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.create_template(
            company_id=current_user.company_id,
            name=body.name,
            default_priority=body.default_priority,
            description=body.description,
            recurrence_frequency=body.recurrence_frequency,
            recurrence_interval=body.recurrence_interval,
            asset_type_filter=body.asset_type_filter,
            checklist_items=[i.model_dump() for i in body.checklist_items],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/v1/maintenance-templates")
def list_maintenance_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(True),
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    templates, total = controller.list_templates(
        company_id=current_user.company_id,
        page=page,
        page_size=page_size,
        is_active=is_active,
    )
    return {
        "data": templates,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/api/v1/maintenance-templates/{template_id}")
def get_maintenance_template(
    template_id: str,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.get_template(
            company_id=current_user.company_id,
            template_id=template_id,
        )
    except GetTemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/api/v1/maintenance-templates/{template_id}")
def update_maintenance_template(
    template_id: str,
    body: UpdateMaintenanceTemplateRequest,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.update_template(
            company_id=current_user.company_id,
            template_id=template_id,
            name=body.name,
            default_priority=body.default_priority,
            description=body.description,
            recurrence_frequency=body.recurrence_frequency,
            recurrence_interval=body.recurrence_interval,
            asset_type_filter=body.asset_type_filter,
            checklist_items=(
                [i.model_dump() for i in body.checklist_items]
                if body.checklist_items is not None
                else None
            ),
        )
    except UpdateTemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/api/v1/maintenance-templates/{template_id}")
def delete_maintenance_template(
    template_id: str,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.delete_template(
            company_id=current_user.company_id,
            template_id=template_id,
        )
    except DeleteTemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/v1/maintenance-templates/{template_id}/apply")
def apply_maintenance_template(
    template_id: str,
    body: ApplyTemplateRequest,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.apply_template(
            company_id=current_user.company_id,
            template_id=template_id,
            asset_ids=body.asset_ids,
            first_due_at=body.first_due_at,
        )
    except ApplyTemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/v1/maintenance-plans")
def list_maintenance_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(True),
    template_id: str | None = Query(None),
    asset_id: str | None = Query(None),
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    plans, total = controller.list_plans(
        company_id=current_user.company_id,
        page=page,
        page_size=page_size,
        is_active=is_active,
        template_id=template_id,
        asset_id=asset_id,
    )
    return {
        "data": plans,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/api/v1/maintenance-plans/{plan_id}")
def get_maintenance_plan(
    plan_id: str,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.get_plan(
            company_id=current_user.company_id,
            plan_id=plan_id,
        )
    except GetPlanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api/v1/maintenance-plans/{plan_id}")
def deactivate_maintenance_plan(
    plan_id: str,
    current_user: User = Depends(admin_dep),
    controller: MaintenanceTemplatesController = Depends(
        get_maintenance_templates_controller,
    ),
):
    try:
        return controller.deactivate_plan(
            company_id=current_user.company_id,
            plan_id=plan_id,
        )
    except DeactivatePlanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
