from fastapi import APIRouter, Depends

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.settings.sla_escalation_dependencies import (
    get_sla_escalation_config_repo,
)
from adapters.http.api.settings.sla_escalation_schemas import (
    SaveSlaEscalationConfigRequest,
    SlaEscalationConfigResponse,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.sla_escalation_config.application.commands.save_config import (
    SaveSlaEscalationConfigCommand,
    SaveSlaEscalationConfigCommandHandler,
)
from src.company_bc.sla_escalation_config.application.queries.get_config import (
    GetSlaEscalationConfigQuery,
    GetSlaEscalationConfigQueryHandler,
)
from src.company_bc.sla_escalation_config.infrastructure.repository import (
    SlaEscalationConfigRepository,
)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
)


@router.get("/sla-escalation")
def get_sla_escalation(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    config_repo: SlaEscalationConfigRepository = Depends(
        get_sla_escalation_config_repo,
    ),
):
    handler = GetSlaEscalationConfigQueryHandler(config_repo=config_repo)
    dto = handler.handle(
        GetSlaEscalationConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": SlaEscalationConfigResponse(
            enabled=dto.enabled,
        ).model_dump(mode="json"),
    }


@router.put("/sla-escalation")
def save_sla_escalation(
    body: SaveSlaEscalationConfigRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    config_repo: SlaEscalationConfigRepository = Depends(
        get_sla_escalation_config_repo,
    ),
):
    handler = SaveSlaEscalationConfigCommandHandler(config_repo=config_repo)
    handler.handle(
        SaveSlaEscalationConfigCommand(
            company_id=current_user.company_id,
            enabled=body.enabled,
            performed_by=current_user.id,
        )
    )

    query_handler = GetSlaEscalationConfigQueryHandler(
        config_repo=config_repo,
    )
    dto = query_handler.handle(
        GetSlaEscalationConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": SlaEscalationConfigResponse(
            enabled=dto.enabled,
        ).model_dump(mode="json"),
    }
