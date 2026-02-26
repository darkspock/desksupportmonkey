from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.checkouts.dependencies import (
    get_asset_repo,
    get_checkout_repo,
    get_maintenance_creator,
    get_user_repo,
)
from adapters.http.api.checkouts.schemas import (
    CancelCheckoutRequest,
    CheckinRequest,
    CheckoutResponse,
    CreateCheckoutRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_bc.checkout.application.commands.accept_checkout import (
    AcceptCheckoutCommand,
    AcceptCheckoutCommandHandler,
)
from src.asset_bc.checkout.application.commands.cancel_checkout import (
    CancelCheckoutCommand,
    CancelCheckoutCommandHandler,
)
from src.asset_bc.checkout.application.commands.checkin_asset import (
    AssetNotFoundError as CheckinAssetNotFoundError,
    CheckinAssetCommand,
    CheckinAssetCommandHandler,
)
from src.asset_bc.checkout.application.commands.create_checkout import (
    AssetNotFoundError as CreateAssetNotFoundError,
    CreateCheckoutCommand,
    CreateCheckoutCommandHandler,
    UserNotFoundError,
)
from src.asset_bc.checkout.application.dtos import CheckoutDto
from src.asset_bc.checkout.application.ports import MaintenanceRecordCreator
from src.asset_bc.checkout.application.queries.get_current_checkout import (
    GetCurrentCheckoutQuery,
    GetCurrentCheckoutQueryHandler,
)
from src.asset_bc.checkout.application.queries.list_asset_checkouts import (
    ListAssetCheckoutsQuery,
    ListAssetCheckoutsQueryHandler,
)
from src.asset_bc.checkout.application.queries.list_company_checkouts import (
    ListCompanyCheckoutsQuery,
    ListCompanyCheckoutsQueryHandler,
)
from src.asset_bc.checkout.domain.exceptions import (
    ActiveCheckoutExistsError,
    AssetAssignedToOtherError,
    CheckoutAlreadyAcceptedError,
    CheckoutNotOpenError,
    InvalidCheckoutAssetStatusError,
    NoActiveCheckoutError,
    UnauthorizedAcceptError,
)
from src.asset_bc.checkout.infrastructure.repository import CheckoutRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository

router = APIRouter(prefix="/api/v1/checkouts", tags=["checkouts"])


def _to_response(dto: CheckoutDto) -> CheckoutResponse:
    return CheckoutResponse(
        id=dto.id,
        asset_id=dto.asset_id,
        user_id=dto.user_id,
        checked_out_by=dto.checked_out_by,
        checked_out_at=dto.checked_out_at,
        condition_out=dto.condition_out,
        condition_out_notes=dto.condition_out_notes,
        notes_out=dto.notes_out,
        accepted_at=dto.accepted_at,
        checked_in_at=dto.checked_in_at,
        checked_in_by=dto.checked_in_by,
        condition_in=dto.condition_in,
        condition_in_notes=dto.condition_in_notes,
        notes_in=dto.notes_in,
        cancelled_at=dto.cancelled_at,
        cancelled_by=dto.cancelled_by,
        cancel_reason=dto.cancel_reason,
        maintenance_id=dto.maintenance_id,
        auto_assigned=dto.auto_assigned,
        status=dto.status,
        created_at=dto.created_at,
    )


# ── POST /checkouts/assets/{asset_id} — Create checkout ──────────────


@router.post("/assets/{asset_id}", status_code=status.HTTP_201_CREATED)
def create_checkout(
    asset_id: str,
    body: CreateCheckoutRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = CreateCheckoutCommandHandler(
        asset_repo=asset_repo,
        checkout_repo=checkout_repo,
        user_repo=user_repo,  # type: ignore[arg-type]
    )
    try:
        handler.handle(
            CreateCheckoutCommand(
                checkout_id=str(ulid.new()),
                company_id=company_id,
                asset_id=asset_id,
                user_id=body.user_id,
                performed_by=current_user.id,
                condition_out=body.condition_out,
                condition_out_notes=body.condition_out_notes,
                notes_out=body.notes_out,
            )
        )
    except CreateAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except ActiveCheckoutExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset already has an active checkout")
    except AssetAssignedToOtherError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidCheckoutAssetStatusError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    checkout = GetCurrentCheckoutQueryHandler(checkout_repo).handle(
        GetCurrentCheckoutQuery(asset_id=asset_id, company_id=company_id)
    )
    if not checkout:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Checkout not found after creation")
    return {"data": _to_response(checkout).model_dump(mode="json")}


# ── POST /checkouts/assets/{asset_id}/checkin — Check in ─────────────


@router.post("/assets/{asset_id}/checkin")
def checkin_asset(
    asset_id: str,
    body: CheckinRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
    maintenance_creator: MaintenanceRecordCreator = Depends(get_maintenance_creator),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = CheckinAssetCommandHandler(
        asset_repo=asset_repo,
        checkout_repo=checkout_repo,
        maintenance_creator=maintenance_creator,
    )
    try:
        handler.handle(
            CheckinAssetCommand(
                asset_id=asset_id,
                company_id=company_id,
                performed_by=current_user.id,
                condition_in=body.condition_in,
                condition_in_notes=body.condition_in_notes,
                notes_in=body.notes_in,
            )
        )
    except CheckinAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except NoActiveCheckoutError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active checkout for this asset")
    except CheckoutNotOpenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Checkout is not open")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return {"data": {"message": "Asset checked in successfully"}}


# ── POST /checkouts/assets/{asset_id}/cancel — Cancel ────────────────


@router.post("/assets/{asset_id}/cancel")
def cancel_checkout(
    asset_id: str,
    body: CancelCheckoutRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = CancelCheckoutCommandHandler(
        asset_repo=asset_repo,
        checkout_repo=checkout_repo,
    )
    try:
        handler.handle(
            CancelCheckoutCommand(
                asset_id=asset_id,
                company_id=company_id,
                performed_by=current_user.id,
                reason=body.reason or "",
            )
        )
    except NoActiveCheckoutError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active checkout for this asset")
    except CheckoutNotOpenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Checkout is not open")

    return {"data": {"message": "Checkout cancelled"}}


# ── POST /checkouts/assets/{asset_id}/accept — Accept (employee) ─────


@router.post("/assets/{asset_id}/accept")
def accept_checkout(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = AcceptCheckoutCommandHandler(
        asset_repo=asset_repo,
        checkout_repo=checkout_repo,
    )
    try:
        handler.handle(
            AcceptCheckoutCommand(
                asset_id=asset_id,
                company_id=company_id,
                user_id=current_user.id,
            )
        )
    except NoActiveCheckoutError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active checkout for this asset")
    except UnauthorizedAcceptError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the assigned user for this checkout")
    except CheckoutAlreadyAcceptedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Checkout already accepted")
    except CheckoutNotOpenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Checkout is not open")

    return {"data": {"message": "Checkout accepted"}}


# ── GET /checkouts/assets/{asset_id}/current — Current checkout ──────


@router.get("/assets/{asset_id}/current")
def get_current_checkout(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = GetCurrentCheckoutQueryHandler(checkout_repo)
    checkout = handler.handle(
        GetCurrentCheckoutQuery(
            asset_id=asset_id,
            company_id=company_id,
        )
    )
    if not checkout:
        return {"data": None}
    return {"data": _to_response(checkout).model_dump(mode="json")}


# ── GET /checkouts/assets/{asset_id} — Asset checkout history ────────


@router.get("/assets/{asset_id}")
def list_asset_checkouts(
    asset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = ListAssetCheckoutsQueryHandler(checkout_repo)
    checkouts, total = handler.handle(
        ListAssetCheckoutsQuery(
            asset_id=asset_id,
            company_id=company_id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [_to_response(c).model_dump(mode="json") for c in checkouts],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


# ── GET /checkouts — Company-wide open checkouts ─────────────────────


@router.get("")
def list_company_checkouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    company_id: str = current_user.company_id  # type: ignore[assignment]
    handler = ListCompanyCheckoutsQueryHandler(checkout_repo)
    checkouts, total = handler.handle(
        ListCompanyCheckoutsQuery(
            company_id=company_id,
            page=page,
            page_size=page_size,
            user_id=user_id,
            asset_id=asset_id,
        )
    )
    return {
        "data": [_to_response(c).model_dump(mode="json") for c in checkouts],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }
