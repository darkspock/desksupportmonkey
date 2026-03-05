import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.my.schemas import AIChatRequest
from core.config import settings
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.company_bc.nav_config.infrastructure.repository import NavConfigRepository
from src.support_bc.ai_assistant.application.commands.ai_chat import (
    AIChatCommand,
    AIChatCommandHandler,
)
from src.support_bc.ai_assistant.domain.exceptions import (
    AIRateLimitExceededError,
    AIUnavailableError,
)
from src.support_bc.ai_assistant.infrastructure.provider_factory import (
    get_ai_provider,
    get_fallback_provider,
)

router = APIRouter(prefix="/api/v1/my", tags=["ai-support"])


def _get_redis():
    return redis.Redis.from_url(settings.celery.CELERY_BROKER_URL, decode_responses=True)


@router.post("/ai-support", status_code=status.HTTP_200_OK)
def ai_chat(
    body: AIChatRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    company = CompanyRepository(db).find_by_id(current_user.company_id)
    nav_config = NavConfigRepository(db).find_by_company(current_user.company_id)

    # Derive enabled modules from hidden_nav_items (keys = sections)
    enabled_modules: list[str] = []
    if nav_config and nav_config.hidden_nav_items:
        # All known sections minus fully-hidden ones
        enabled_modules = list(nav_config.hidden_nav_items.keys())

    handler = AIChatCommandHandler(
        primary_provider=get_ai_provider(),
        fallback_provider=get_fallback_provider(),
        redis_client=_get_redis(),
    )
    try:
        handler.handle(
            AIChatCommand(
                user_id=current_user.id,
                company_id=current_user.company_id or "",
                company_name=company.name if company else "",
                plan_tier=company.plan.value if company else "free",
                enabled_modules=enabled_modules,
                messages=[{"role": m.role, "content": m.content} for m in body.messages],
            )
        )
    except AIRateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: max 20 AI queries per hour. Please try again later.",
        )
    except AIUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return {"data": {"response": handler.response}}
