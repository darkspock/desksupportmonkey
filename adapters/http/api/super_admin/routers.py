import dataclasses
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from adapters.http.api.audit.schemas import AuditEntryListResponse
from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.super_admin.dependencies import (
    get_audit_repo,
    get_company_repo,
    get_stripe_client,
)
from adapters.http.api.super_admin.schemas import FounderDashboardResponse
from adapters.http.schemas.responses import PaginationMeta
from core.stripe_client import StripeClient
from src.audit_bc.audit.infrastructure.repository import AuditRepository
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


@router.get("/audit")
def list_cross_company_audit(
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    search: Optional[str] = None,
):
    filters = {
        "page": page,
        "page_size": page_size,
        "company_id": company_id,
        "date_from": date_from,
        "date_to": date_to,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "search": search,
    }
    entries, total = audit_repo.find_all_cross_company(filters)
    data = [
        AuditEntryListResponse(
            id=e.id,
            actor_email=e.actor_email,
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            http_method=e.http_method,
            response_status=e.response_status,
            ip_address=e.ip_address,
            created_at=e.created_at,
            tag_count=0,
        ).model_dump(mode="json")
        for e in entries
    ]
    return {
        "data": data,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }
