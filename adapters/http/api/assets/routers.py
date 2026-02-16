import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.assets.schemas import (
    AssignableUserResponse,
    AssetEventResponse,
    AssetResponse,
    AssignAssetRequest,
    ChangeStatusRequest,
    CreateAssetRequest,
    ImportResponse,
    ImportRowErrorResponse,
    UpdateAssetRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.asset_bc.asset.application.commands.create_asset import (
    CreateAssetCommand,
    CreateAssetCommandHandler,
    SerialNumberExistsError,
)
from src.asset_bc.asset.application.commands.update_asset import (
    AssetNotFoundError as UpdateAssetNotFoundError,
    UpdateAssetCommand,
    UpdateAssetCommandHandler,
)
from src.asset_bc.asset.application.commands.change_asset_status import (
    AssetNotFoundError as StatusAssetNotFoundError,
    ChangeAssetStatusCommand,
    ChangeAssetStatusCommandHandler,
)
from src.asset_bc.asset.application.queries.list_assets import (
    ListAssetsQuery,
    ListAssetsQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset import (
    AssetNotFoundError as GetAssetNotFoundError,
    GetAssetQuery,
    GetAssetQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset_history import (
    AssetNotFoundError as HistoryAssetNotFoundError,
    GetAssetHistoryQuery,
    GetAssetHistoryQueryHandler,
)
from src.asset_bc.asset.application.commands.assign_asset import (
    AssetNotFoundError as AssignAssetNotFoundError,
    AssignAssetCommand,
    AssignAssetCommandHandler,
    UserNotFoundError,
    UserInactiveError,
)
from src.asset_bc.asset.application.commands.unassign_asset import (
    AssetNotFoundError as UnassignAssetNotFoundError,
    UnassignAssetCommand,
    UnassignAssetCommandHandler,
)
from src.asset_bc.asset.application.commands.import_assets import (
    ImportAssetsCommand,
    ImportAssetsCommandHandler,
    InvalidCSVError,
)
from src.asset_bc.asset.domain.entities import Asset, AssetEvent, InvalidAssignmentError
from src.asset_bc.asset.domain.enums import InvalidStatusTransitionError
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


def _to_response(asset: Asset, assigned_to_email: str | None = None) -> AssetResponse:
    return AssetResponse(
        id=asset.id,
        company_id=asset.company_id,
        type=asset.type.value,
        brand=asset.brand,
        model=asset.model,
        serial_number=asset.serial_number,
        status=asset.status.value,
        assigned_to=asset.assigned_to,
        assigned_to_email=assigned_to_email,
        department_id=asset.department_id,
        purchase_date=asset.purchase_date,
        warranty_expiration=asset.warranty_expiration,
        notes=asset.notes,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _event_to_response(event: AssetEvent, performed_by_email: str | None = None) -> AssetEventResponse:
    return AssetEventResponse(
        id=event.id,
        asset_id=event.asset_id,
        event_type=event.event_type,
        data=event.data,
        performed_by=event.performed_by,
        performed_by_email=performed_by_email,
        created_at=event.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(
    body: CreateAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = CreateAssetCommandHandler(asset_repo=AssetRepository(db))
    try:
        asset = handler.handle(
            CreateAssetCommand(
                company_id=current_user.company_id,
                type=body.type,
                brand=body.brand,
                model=body.model,
                serial_number=body.serial_number,
                purchase_date=body.purchase_date,
                warranty_expiration=body.warranty_expiration,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except SerialNumberExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset with this serial number already exists",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"data": _to_response(asset).model_dump(mode="json")}


@router.get("")
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = ListAssetsQueryHandler(asset_repo=AssetRepository(db))
    assets, total = handler.handle(
        ListAssetsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            search=search,
            type=type,
            status=status,
            department_id=department_id,
            assigned_to=assigned_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    )
    user_repo = UserRepository(db)
    assigned_ids = [a.assigned_to for a in assets if a.assigned_to]
    user_map = user_repo.find_by_ids(assigned_ids)
    return {
        "data": [
            _to_response(
                a,
                assigned_to_email=user_map[a.assigned_to].email if a.assigned_to and a.assigned_to in user_map else None,
            ).model_dump(mode="json")
            for a in assets
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_assets(
    file: UploadFile,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    if file.size and file.size > 1_048_576:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 1MB limit",
        )
    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be UTF-8 encoded",
        )
    handler = ImportAssetsCommandHandler(asset_repo=AssetRepository(db))
    try:
        result = handler.handle(
            ImportAssetsCommand(
                company_id=current_user.company_id,
                performed_by=current_user.id,
                csv_content=csv_content,
            )
        )
    except InvalidCSVError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return {
        "data": ImportResponse(
            total=result.total,
            successful=result.successful,
            failed=[
                ImportRowErrorResponse(row=e.row, error=e.error)
                for e in result.failed
            ],
        ).model_dump()
    }


@router.get("/assignable-users")
def list_assignable_users(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    users, _ = UserRepository(db).find_all_by_company(
        company_id=current_user.company_id,
        page=1,
        page_size=500,
        is_active=True,
    )
    return {
        "data": [
            AssignableUserResponse(id=u.id, email=u.email, name=u.name).model_dump(mode="json")
            for u in users
        ]
    }


@router.get("/{asset_id}")
def get_asset(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = GetAssetQueryHandler(asset_repo=AssetRepository(db))
    try:
        asset = handler.handle(
            GetAssetQuery(asset_id=asset_id, company_id=current_user.company_id)
        )
    except GetAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = UserRepository(db).find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email).model_dump(mode="json")}


@router.put("/{asset_id}")
def update_asset(
    asset_id: str,
    body: UpdateAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = UpdateAssetCommandHandler(asset_repo=AssetRepository(db))
    try:
        asset = handler.handle(
            UpdateAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                brand=body.brand,
                model=body.model,
                notes=body.notes,
                purchase_date=body.purchase_date,
                warranty_expiration=body.warranty_expiration,
            )
        )
    except UpdateAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = UserRepository(db).find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email).model_dump(mode="json")}


@router.patch("/{asset_id}/status")
def change_asset_status(
    asset_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = ChangeAssetStatusCommandHandler(asset_repo=AssetRepository(db))
    try:
        asset = handler.handle(
            ChangeAssetStatusCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                new_status=body.status,
                performed_by=current_user.id,
            )
        )
    except StatusAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = UserRepository(db).find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email).model_dump(mode="json")}


@router.get("/{asset_id}/history")
def get_asset_history(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = GetAssetHistoryQueryHandler(asset_repo=AssetRepository(db))
    try:
        events = handler.handle(
            GetAssetHistoryQuery(asset_id=asset_id, company_id=current_user.company_id)
        )
    except HistoryAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    user_map = UserRepository(db).find_by_ids([e.performed_by for e in events])
    return {
        "data": [
            _event_to_response(
                e,
                performed_by_email=user_map[e.performed_by].email if e.performed_by in user_map else None,
            ).model_dump(mode="json")
            for e in events
        ]
    }


@router.patch("/{asset_id}/assign")
def assign_asset(
    asset_id: str,
    body: AssignAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = AssignAssetCommandHandler(
        asset_repo=AssetRepository(db),
        user_repo=UserRepository(db),
    )
    try:
        asset = handler.handle(
            AssignAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                user_id=body.user_id,
                performed_by=current_user.id,
            )
        )
    except AssignAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserInactiveError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is inactive")
    except InvalidAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = UserRepository(db).find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email).model_dump(mode="json")}


@router.patch("/{asset_id}/unassign")
def unassign_asset(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    handler = UnassignAssetCommandHandler(asset_repo=AssetRepository(db))
    try:
        asset = handler.handle(
            UnassignAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except UnassignAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except InvalidAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"data": _to_response(asset, assigned_to_email=None).model_dump(mode="json")}
