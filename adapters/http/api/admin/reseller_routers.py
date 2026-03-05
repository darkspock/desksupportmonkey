import ulid
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.reseller.dependencies import (
    get_reseller_command_bus,
    get_reseller_query_bus,
)
from adapters.http.api.reseller.mappers import CommissionMapper, ResellerClientMapper, ResellerMapper
from adapters.http.api.reseller.schemas import (
    CreateResellerRequest,
    RejectResellerRequest,
    UpdateResellerSettingsRequest,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.framework.application.command_bus import CommandBus
from src.framework.application.query_bus import QueryBus
from src.reseller_bc.reseller.application.commands.approve_reseller import (
    ApproveResellerCommand,
)
from src.reseller_bc.reseller.application.commands.create_reseller import (
    CreateResellerCommand,
)
from src.reseller_bc.reseller.application.commands.reject_reseller import (
    RejectResellerCommand,
)
from src.reseller_bc.reseller.application.commands.update_reseller import (
    UpdateResellerCommand,
)
from src.reseller_bc.reseller.application.queries.get_reseller_by_id import (
    GetResellerByIdQuery,
)
from src.reseller_bc.reseller.application.queries.list_resellers import (
    ListResellersQuery,
)
from src.reseller_bc.reseller.domain.exceptions import (
    InvalidCommissionRateException,
    InvalidMinPayoutException,
    ReferralCodeCollisionException,
    ResellerAlreadyExistsException,
    ResellerNotFoundException,
    ResellerPendingApprovalException,
)

router = APIRouter(prefix="/api/v1/admin/resellers", tags=["admin-resellers"])


@router.post("/", status_code=201)
def create_reseller(
    body: CreateResellerRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    reseller_id = str(ulid.new())
    try:
        cmd_bus.dispatch(CreateResellerCommand(
            id=reseller_id,
            email=body.email,
            name=body.name,
            commission_pct=body.commission_pct,
            min_payout_cents=body.min_payout_cents,
        ))
    except ResellerAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidCommissionRateException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidMinPayoutException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ReferralCodeCollisionException as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Return created reseller
    dto = query_bus.query(GetResellerByIdQuery(reseller_id=reseller_id))
    if dto is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve created reseller")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.get("/")
def list_resellers(
    offset: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    dto = query_bus.query(ListResellersQuery(offset=offset, limit=limit))
    return {"data": ResellerMapper.dto_to_list_response(dto).model_dump()}


@router.get("/{reseller_id}")
def get_reseller(
    reseller_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    dto = query_bus.query(GetResellerByIdQuery(reseller_id=reseller_id))
    if dto is None:
        raise HTTPException(status_code=404, detail=f"Reseller not found: {reseller_id}")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.patch("/{reseller_id}")
def update_reseller(
    reseller_id: str,
    body: UpdateResellerSettingsRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    try:
        cmd_bus.dispatch(UpdateResellerCommand(
            reseller_id=reseller_id,
            name=body.name,
            email=body.email,
            company_name=body.company_name,
            tax_id=body.tax_id,
            referral_code=body.referral_code,
            commission_pct=body.commission_pct,
            min_payout_cents=body.min_payout_cents,
            status=body.status,
        ))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidCommissionRateException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidMinPayoutException as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Return updated reseller
    dto = query_bus.query(GetResellerByIdQuery(reseller_id=reseller_id))
    if dto is None:
        raise HTTPException(status_code=404, detail="Reseller not found")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.get("/{reseller_id}/clients")
def list_reseller_clients(
    reseller_id: str,
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.client.application.queries.list_reseller_clients import ListResellerClientsQuery

    dto = query_bus.query(ListResellerClientsQuery(
        reseller_id=reseller_id,
        offset=offset,
        limit=limit,
    ))
    return {"data": ResellerClientMapper.dto_to_list_response(dto).model_dump()}


@router.get("/{reseller_id}/commissions")
def list_reseller_commissions(
    reseller_id: str,
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    from src.reseller_bc.commission.application.queries.list_commissions import ListCommissionsQuery

    dto = query_bus.query(ListCommissionsQuery(
        reseller_id=reseller_id, offset=offset, limit=limit,
    ))
    return {"data": CommissionMapper.dto_to_list_response(dto).model_dump()}


@router.post("/{reseller_id}/approve")
def approve_reseller(
    reseller_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
    query_bus: QueryBus = Depends(get_reseller_query_bus),
):
    try:
        cmd_bus.dispatch(ApproveResellerCommand(reseller_id=reseller_id))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ResellerPendingApprovalException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ReferralCodeCollisionException as e:
        raise HTTPException(status_code=500, detail=str(e))

    dto = query_bus.query(GetResellerByIdQuery(reseller_id=reseller_id))
    if dto is None:
        raise HTTPException(status_code=404, detail="Reseller not found")
    return {"data": ResellerMapper.dto_to_response(dto).model_dump()}


@router.post("/{reseller_id}/reject")
def reject_reseller(
    reseller_id: str,
    body: RejectResellerRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    cmd_bus: CommandBus = Depends(get_reseller_command_bus),
):
    try:
        cmd_bus.dispatch(RejectResellerCommand(
            reseller_id=reseller_id, reason=body.reason,
        ))
    except ResellerNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ResellerPendingApprovalException as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"message": "Reseller application rejected."}
