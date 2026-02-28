from datetime import datetime
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.sla.dependencies import (
    get_asset_repo,
    get_request_repo,
    get_sla_escalation_config_repo,
    get_sla_repo,
)
from adapters.http.api.sla.schemas import (
    BreachTrendPointResponse,
    ComplianceByGroupResponse,
    CreateSlaPolicyRequest,
    SlaDashboardResponse,
    SlaPolicyResponse,
    UpdateSlaPolicyRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.sla_bc.sla.application.commands.create_policy import (
    CreateSlaPolicyCommand,
    CreateSlaPolicyCommandHandler,
)
from src.sla_bc.sla.application.commands.deactivate_policy import (
    DeactivateSlaPolicyCommand,
    DeactivateSlaPolicyCommandHandler,
)
from src.sla_bc.sla.application.commands.update_policy import (
    UpdateSlaPolicyCommand,
    UpdateSlaPolicyCommandHandler,
)
from src.sla_bc.sla.application.queries.get_policy import (
    GetSlaPolicyQuery,
    GetSlaPolicyQueryHandler,
)
from src.sla_bc.sla.application.queries.list_policies import (
    ListSlaPoliciesQuery,
    ListSlaPoliciesQueryHandler,
)
from src.sla_bc.sla.application.queries.get_dashboard import (
    GetSlaDashboardQuery,
    GetSlaDashboardQueryHandler,
)
from src.sla_bc.sla.application.queries.get_request_sla import (
    GetRequestSlaStatusQuery,
    GetRequestSlaStatusQueryHandler,
)
from src.sla_bc.sla.domain.exceptions import (
    DuplicateSlaPolicyError,
    InvalidSlaTargetsError,
    SlaPolicyNotFoundError,
)
from src.sla_bc.sla.infrastructure.repository import SlaRepository

router = APIRouter(prefix="/api/v1/sla", tags=["sla"])


def _policy_response(dto) -> dict:
    return SlaPolicyResponse(
        id=dto.id,
        company_id=dto.company_id,
        name=dto.name,
        priority=dto.priority,
        request_type=dto.request_type,
        response_time_hours=dto.response_time_hours,
        resolution_time_hours=dto.resolution_time_hours,
        warning_threshold_pct=dto.warning_threshold_pct,
        escalate_on_breach=dto.escalate_on_breach,
        is_active=dto.is_active,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    ).model_dump(mode="json")


# ---- Policies ----


@router.post("/policies", status_code=201)
def create_policy(
    body: CreateSlaPolicyRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    policy_id = str(ulid.new())
    handler = CreateSlaPolicyCommandHandler(sla_repo=repo)
    try:
        handler.handle(
            CreateSlaPolicyCommand(
                policy_id=policy_id,
                company_id=current_user.company_id,
                name=body.name,
                priority=body.priority,
                response_time_hours=body.response_time_hours,
                resolution_time_hours=body.resolution_time_hours,
                request_type=body.request_type,
                warning_threshold_pct=body.warning_threshold_pct,
                escalate_on_breach=body.escalate_on_breach,
            )
        )
    except InvalidSlaTargetsError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DuplicateSlaPolicyError as e:
        raise HTTPException(status_code=409, detail=str(e))

    query_handler = GetSlaPolicyQueryHandler(sla_repo=repo)
    dto = query_handler.handle(
        GetSlaPolicyQuery(policy_id=policy_id, company_id=current_user.company_id)
    )
    return {"data": _policy_response(dto)}


@router.get("/policies")
def list_policies(
    is_active: Optional[bool] = Query(default=None),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    handler = ListSlaPoliciesQueryHandler(sla_repo=repo)
    policies = handler.handle(
        ListSlaPoliciesQuery(
            company_id=current_user.company_id,
            is_active=is_active,
        )
    )
    return {"data": [_policy_response(p) for p in policies]}


@router.get("/policies/{policy_id}")
def get_policy(
    policy_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    handler = GetSlaPolicyQueryHandler(sla_repo=repo)
    try:
        dto = handler.handle(
            GetSlaPolicyQuery(
                policy_id=policy_id,
                company_id=current_user.company_id,
            )
        )
    except SlaPolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"data": _policy_response(dto)}


@router.put("/policies/{policy_id}")
def update_policy(
    policy_id: str,
    body: UpdateSlaPolicyRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    handler = UpdateSlaPolicyCommandHandler(sla_repo=repo)
    try:
        handler.handle(
            UpdateSlaPolicyCommand(
                policy_id=policy_id,
                company_id=current_user.company_id,
                name=body.name,
                response_time_hours=body.response_time_hours,
                resolution_time_hours=body.resolution_time_hours,
                warning_threshold_pct=body.warning_threshold_pct,
                escalate_on_breach=body.escalate_on_breach,
            )
        )
    except SlaPolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidSlaTargetsError as e:
        raise HTTPException(status_code=422, detail=str(e))

    query_handler = GetSlaPolicyQueryHandler(sla_repo=repo)
    dto = query_handler.handle(
        GetSlaPolicyQuery(
            policy_id=policy_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _policy_response(dto)}


@router.delete("/policies/{policy_id}", status_code=204)
def deactivate_policy(
    policy_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    handler = DeactivateSlaPolicyCommandHandler(sla_repo=repo)
    try:
        handler.handle(
            DeactivateSlaPolicyCommand(
                policy_id=policy_id,
                company_id=current_user.company_id,
            )
        )
    except SlaPolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- SLA Status ----


@router.get("/requests/{request_id}/status")
def get_request_sla_status(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    sla_repo: SlaRepository = Depends(get_sla_repo),
    request_repo=Depends(get_request_repo),
    asset_repo=Depends(get_asset_repo),
    escalation_config_repo=Depends(get_sla_escalation_config_repo),
):
    handler = GetRequestSlaStatusQueryHandler(
        sla_repo=sla_repo,
        request_repo=request_repo,
        asset_repo=asset_repo,
        escalation_config_repo=escalation_config_repo,
    )
    dto = handler.handle(
        GetRequestSlaStatusQuery(
            request_id=request_id,
            company_id=current_user.company_id,
        )
    )
    if not dto:
        return {"data": None}
    return {
        "data": {
            "policy_name": dto.policy_name,
            "response_target_hours": dto.response_target_hours,
            "resolution_target_hours": dto.resolution_target_hours,
            "response_elapsed_hours": dto.response_elapsed_hours,
            "resolution_elapsed_hours": dto.resolution_elapsed_hours,
            "response_status": dto.response_status,
            "resolution_status": dto.resolution_status,
            "response_remaining_hours": dto.response_remaining_hours,
            "resolution_remaining_hours": dto.resolution_remaining_hours,
            "escalated": dto.escalated,
            "effective_priority": dto.effective_priority,
            "original_priority": dto.original_priority,
        }
    }


# ---- Dashboard ----


@router.get("/dashboard")
def get_sla_dashboard(
    from_date: datetime,
    to_date: datetime,
    bucket: str = Query(default="week", pattern=r"^(day|week|month)$"),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    repo: SlaRepository = Depends(get_sla_repo),
):
    handler = GetSlaDashboardQueryHandler(sla_repo=repo)
    dto = handler.handle(
        GetSlaDashboardQuery(
            company_id=current_user.company_id,
            from_date=from_date,
            to_date=to_date,
            bucket=bucket,
        )
    )
    return {
        "data": SlaDashboardResponse(
            total_resolved=dto.total_resolved,
            met=dto.met,
            breached=dto.breached,
            compliance_pct=dto.compliance_pct,
            by_priority=[
                ComplianceByGroupResponse(
                    group=g.group,
                    total=g.total,
                    met=g.met,
                    breached=g.breached,
                    compliance_pct=g.compliance_pct,
                )
                for g in dto.by_priority
            ],
            by_type=[
                ComplianceByGroupResponse(
                    group=g.group,
                    total=g.total,
                    met=g.met,
                    breached=g.breached,
                    compliance_pct=g.compliance_pct,
                )
                for g in dto.by_type
            ],
            breach_trend=[
                BreachTrendPointResponse(period=t.period, count=t.count)
                for t in dto.breach_trend
            ],
        ).model_dump(mode="json")
    }
