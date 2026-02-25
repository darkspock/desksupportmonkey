import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.settings.nav_config_dependencies import (
    get_nav_config_repo,
)
from adapters.http.api.settings.nav_config_schemas import (
    NavConfigResponse,
    SaveNavConfigRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.nav_config.application.commands.save_nav_config import (
    InvalidRoleError,
    SaveNavConfigCommand,
    SaveNavConfigCommandHandler,
)
from src.company_bc.nav_config.application.queries.get_nav_config import (
    GetNavConfigQuery,
    GetNavConfigQueryHandler,
)
from src.company_bc.nav_config.infrastructure.repository import (
    NavConfigRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
)


@router.get("/nav-visibility")
def get_nav_visibility(
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    nav_config_repo: NavConfigRepository = Depends(
        get_nav_config_repo,
    ),
):
    handler = GetNavConfigQueryHandler(
        nav_config_repo=nav_config_repo,
    )
    config = handler.handle(
        GetNavConfigQuery(
            company_id=current_user.company_id,
        )
    )
    if not config:
        return {"data": None}
    return {
        "data": NavConfigResponse(
            id=config.id,
            company_id=config.company_id,
            hidden_nav_items=config.hidden_nav_items,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }


@router.put("/nav-visibility")
def save_nav_visibility(
    body: SaveNavConfigRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    nav_config_repo: NavConfigRepository = Depends(
        get_nav_config_repo,
    ),
):
    handler = SaveNavConfigCommandHandler(
        nav_config_repo=nav_config_repo,
    )
    try:
        handler.handle(
            SaveNavConfigCommand(
                company_id=current_user.company_id,
                hidden_nav_items=body.hidden_nav_items,
                performed_by=current_user.id,
            )
        )
    except InvalidRoleError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot configure nav items for admin or super_admin roles",
        )

    query_handler = GetNavConfigQueryHandler(
        nav_config_repo=nav_config_repo,
    )
    config = query_handler.handle(
        GetNavConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": NavConfigResponse(
            id=config.id,
            company_id=config.company_id,
            hidden_nav_items=config.hidden_nav_items,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }
