from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session

from core.database import get_db
from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.reseller.mappers import PayoutMapper
from adapters.http.api.reseller.schemas import ProcessPayoutRequest
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole

router = APIRouter(prefix="/api/v1/admin/payouts", tags=["admin-payouts"])


@router.get("/")
def list_all_payouts(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller_id: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    from src.reseller_bc.payout.application.queries.list_payouts import (
        ListPayoutsQuery,
        ListPayoutsQueryHandler,
    )
    from src.reseller_bc.payout.infrastructure.repository import ResellerPayoutRepository
    from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

    handler = ListPayoutsQueryHandler(
        payout_repo=ResellerPayoutRepository(db),
        reseller_repo=ResellerRepository(db),
    )
    dto = handler.handle(ListPayoutsQuery(
        reseller_id=reseller_id, offset=offset, limit=limit,
    ))
    return {"data": PayoutMapper.dto_to_list_response(dto).model_dump()}


@router.patch("/{payout_id}")
def process_payout(
    payout_id: str,
    body: ProcessPayoutRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
    from src.reseller_bc.payout.application.commands.process_payout import (
        ProcessPayoutCommand,
        ProcessPayoutCommandHandler,
    )
    from src.reseller_bc.payout.application.queries.list_payouts import (
        ListPayoutsQuery,
        ListPayoutsQueryHandler,
    )
    from src.reseller_bc.payout.domain.exceptions import (
        InvalidPayoutTransitionException,
        PayoutNotFoundException,
    )
    from src.reseller_bc.payout.infrastructure.repository import ResellerPayoutRepository
    from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

    payout_repo = ResellerPayoutRepository(db)
    commission_repo = ResellerCommissionRepository(db)

    handler = ProcessPayoutCommandHandler(payout_repo, commission_repo)
    try:
        handler.handle(ProcessPayoutCommand(
            payout_id=payout_id,
            action=body.action,
            processed_by=current_user.id,
            payment_reference=body.payment_reference,
            notes=body.notes,
        ))
    except PayoutNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidPayoutTransitionException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Return updated payout
    query_handler = ListPayoutsQueryHandler(
        payout_repo=payout_repo, reseller_repo=ResellerRepository(db),
    )
    dto = query_handler.handle(ListPayoutsQuery(offset=0, limit=1))
    # Find the specific payout in results
    for item in dto.items:
        if item.id == payout_id:
            return {"data": PayoutMapper.dto_to_response(item).model_dump()}

    # Fallback: query the payout directly
    payout = payout_repo.find_by_id(payout_id)
    if payout:
        reseller_repo = ResellerRepository(db)
        reseller = reseller_repo.get_by_id(payout.reseller_id)
        from src.reseller_bc.payout.application.dtos import PayoutDto
        dto_item = PayoutDto(
            id=payout.id,
            reseller_id=payout.reseller_id,
            reseller_name=reseller.name if reseller else "Unknown",
            amount_cents=payout.amount_cents,
            status=payout.status.value,
            requested_at=payout.requested_at,
            processed_at=payout.processed_at,
            processed_by=payout.processed_by,
            payment_reference=payout.payment_reference,
            notes=payout.notes,
        )
        return {"data": PayoutMapper.dto_to_response(dto_item).model_dump()}
    return {"data": {}}
