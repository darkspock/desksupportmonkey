import dataclasses

from fastapi import APIRouter, Depends

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.super_admin.dependencies import get_company_repo, get_stripe_client
from adapters.http.api.super_admin.schemas import FounderDashboardResponse
from core.stripe_client import StripeClient
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.queries.get_founder_dashboard import (
    GetFounderDashboardQuery,
    GetFounderDashboardQueryHandler,
)
from src.company_bc.company.infrastructure.repository import CompanyRepository

router = APIRouter(prefix="/api/v1/super-admin", tags=["super-admin"])


@router.get("/dashboard")
def get_founder_dashboard(
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    stripe_client: StripeClient = Depends(get_stripe_client),
):
    handler = GetFounderDashboardQueryHandler(
        company_repo=company_repo,
        stripe_client=stripe_client,
    )
    dto = handler.handle(GetFounderDashboardQuery())
    response = FounderDashboardResponse(
        revenue=dataclasses.asdict(dto.revenue),  # type: ignore[arg-type]
        trials=dataclasses.asdict(dto.trials),  # type: ignore[arg-type]
        health=dataclasses.asdict(dto.health),  # type: ignore[arg-type]
        growth=dataclasses.asdict(dto.growth),  # type: ignore[arg-type]
        next_milestone=dataclasses.asdict(dto.next_milestone),  # type: ignore[arg-type]
        upcoming_renewals_7d=[
            dataclasses.asdict(r) for r in dto.upcoming_renewals_7d
        ],
        as_of=dto.as_of,
    )
    return {"data": response.model_dump(mode="json")}
