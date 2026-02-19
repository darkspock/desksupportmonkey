import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import (
    require_role,
)
from adapters.http.api.settings.dependencies import (
    get_config_repo,
)
from adapters.http.api.settings.schemas import (
    AIConfigResponse,
    SaveAIConfigRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.assignment_config.application.commands.save_config import (  # noqa: E501
    InvalidProviderError,
    SaveCompanyAIConfigCommand,
    SaveCompanyAIConfigCommandHandler,
)
from src.company_bc.assignment_config.application.queries.get_config import (  # noqa: E501
    GetCompanyAIConfigQuery,
    GetCompanyAIConfigQueryHandler,
)
from src.company_bc.assignment_config.infrastructure.repository import (  # noqa: E501
    AssignmentConfigRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
)


@router.put("/assignment-ai")
def save_assignment_ai_config(
    body: SaveAIConfigRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    config_repo: AssignmentConfigRepository = Depends(
        get_config_repo,
    ),
):
    handler = SaveCompanyAIConfigCommandHandler(
        config_repo=config_repo,
    )
    try:
        handler.handle(
            SaveCompanyAIConfigCommand(
                company_id=current_user.company_id,
                provider=body.provider,
                prompt_template=body.prompt_template,
                model=body.model,
                performed_by=current_user.id,
            )
        )
    except InvalidProviderError:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="Invalid AI provider",
        )

    query_handler = GetCompanyAIConfigQueryHandler(
        config_repo=config_repo,
    )
    config = query_handler.handle(
        GetCompanyAIConfigQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": AIConfigResponse(
            id=config.id,
            company_id=config.company_id,
            provider=config.provider.value,
            prompt_template=config.prompt_template,
            model=config.model,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }


@router.get("/assignment-ai")
def get_assignment_ai_config(
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    config_repo: AssignmentConfigRepository = Depends(
        get_config_repo,
    ),
):
    handler = GetCompanyAIConfigQueryHandler(
        config_repo=config_repo,
    )
    config = handler.handle(
        GetCompanyAIConfigQuery(
            company_id=current_user.company_id,
        )
    )
    if not config:
        return {"data": None}
    return {
        "data": AIConfigResponse(
            id=config.id,
            company_id=config.company_id,
            provider=config.provider.value,
            prompt_template=config.prompt_template,
            model=config.model,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }
