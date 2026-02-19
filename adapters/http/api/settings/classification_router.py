import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.settings.classification_dependencies import (
    get_classification_config_repo,
)
from adapters.http.api.settings.classification_schemas import (
    ClassificationConfigResponse,
    SaveClassificationConfigRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.classification_config.application.commands.save_config import (
    InvalidProviderError,
    InvalidThresholdError,
    InvalidTimeoutError,
    SaveClassificationConfigCommand,
    SaveClassificationConfigCommandHandler,
)
from src.company_bc.classification_config.application.queries.get_config import (
    GetClassificationConfigQuery,
    GetClassificationConfigQueryHandler,
)
from src.company_bc.classification_config.infrastructure.repository import (
    ClassificationConfigRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
)


@router.put("/request-classification")
def save_classification_config(
    body: SaveClassificationConfigRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    config_repo: ClassificationConfigRepository = Depends(
        get_classification_config_repo,
    ),
):
    assert current_user.company_id is not None
    handler = SaveClassificationConfigCommandHandler(config_repo=config_repo)
    try:
        handler.handle(
            SaveClassificationConfigCommand(
                company_id=current_user.company_id,
                is_enabled=body.is_enabled,
                provider=body.provider,
                model=body.model,
                confidence_threshold=body.confidence_threshold,
                prompt_template=body.prompt_template,
                timeout_seconds=body.timeout_seconds,
                performed_by=current_user.id,
            )
        )
    except InvalidProviderError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid AI provider",
        )
    except InvalidThresholdError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Confidence threshold must be between 0.5 and 1.0",
        )
    except InvalidTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Timeout must be at least 1 second",
        )

    query_handler = GetClassificationConfigQueryHandler(config_repo=config_repo)
    config = query_handler.handle(
        GetClassificationConfigQuery(company_id=current_user.company_id)
    )
    assert config is not None
    return {
        "data": ClassificationConfigResponse(
            id=config.id,
            company_id=config.company_id,
            is_enabled=config.is_enabled,
            provider=config.provider,
            model=config.model,
            confidence_threshold=config.confidence_threshold,
            prompt_template=config.prompt_template,
            timeout_seconds=config.timeout_seconds,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }


@router.get("/request-classification")
def get_classification_config(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    config_repo: ClassificationConfigRepository = Depends(
        get_classification_config_repo,
    ),
):
    assert current_user.company_id is not None
    handler = GetClassificationConfigQueryHandler(config_repo=config_repo)
    config = handler.handle(
        GetClassificationConfigQuery(company_id=current_user.company_id)
    )
    if not config:
        return {"data": None}
    return {
        "data": ClassificationConfigResponse(
            id=config.id,
            company_id=config.company_id,
            is_enabled=config.is_enabled,
            provider=config.provider,
            model=config.model,
            confidence_threshold=config.confidence_threshold,
            prompt_template=config.prompt_template,
            timeout_seconds=config.timeout_seconds,
            created_at=config.created_at,
            updated_at=config.updated_at,
        ).model_dump(mode="json"),
    }
