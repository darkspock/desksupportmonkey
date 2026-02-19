import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import (
    require_role,
)
from adapters.http.api.settings.procurement_dependencies import (  # noqa: E501
    get_procurement_config_repo,
)
from adapters.http.api.settings.procurement_schemas import (
    ProcurementConfigResponse,
    ProcurementConfigUpdateRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.budget.application.commands.save_config import (  # noqa: E501
    SaveProcurementConfigCommand,
    SaveProcurementConfigCommandHandler,
)
from src.procurement_bc.budget.application.queries.get_config import (  # noqa: E501
    GetProcurementConfigQuery,
    GetProcurementConfigQueryHandler,
)
from src.procurement_bc.budget.infrastructure.repository import (  # noqa: E501
    CompanyProcurementConfigRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
)


def _to_response(
    config,
) -> ProcurementConfigResponse:
    return ProcurementConfigResponse(
        id=config.id if config.id else None,
        company_id=config.company_id,
        enforcement_mode=config.enforcement_mode,
        approval_threshold_cents=(
            config.approval_threshold_cents
        ),
        po_number_prefix=config.po_number_prefix,
        fiscal_year_start_month=(
            config.fiscal_year_start_month
        ),
        currency=config.currency,
        auto_create_assets=config.auto_create_assets,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/procurement")
def save_procurement_config(
    body: ProcurementConfigUpdateRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    config_repo: CompanyProcurementConfigRepository = Depends(  # noqa: E501
        get_procurement_config_repo,
    ),
):
    handler = SaveProcurementConfigCommandHandler(
        config_repo=config_repo,
    )
    try:
        handler.handle(
            SaveProcurementConfigCommand(
                company_id=current_user.company_id,
                enforcement_mode=body.enforcement_mode,
                approval_threshold_cents=(
                    body.approval_threshold_cents
                ),
                po_number_prefix=body.po_number_prefix,
                fiscal_year_start_month=(
                    body.fiscal_year_start_month
                ),
                currency=body.currency,
                auto_create_assets=body.auto_create_assets,
                performed_by=current_user.id,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(e),
        )

    query_handler = GetProcurementConfigQueryHandler(
        config_repo=config_repo,
    )
    config = query_handler.handle(
        GetProcurementConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(config).model_dump(
            mode="json",
        ),
    }


@router.get("/procurement")
def get_procurement_config(
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    config_repo: CompanyProcurementConfigRepository = Depends(  # noqa: E501
        get_procurement_config_repo,
    ),
):
    handler = GetProcurementConfigQueryHandler(
        config_repo=config_repo,
    )
    config = handler.handle(
        GetProcurementConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(config).model_dump(
            mode="json",
        ),
    }
