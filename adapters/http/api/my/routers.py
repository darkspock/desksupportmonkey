import logging

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.my.schemas import MyEquipmentResponse, MyRequestResponse
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.request_bc.request.application.queries.my_requests import (
    MyRequestsQuery,
    MyRequestsQueryHandler,
)
from src.request_bc.request.infrastructure.repository import RequestRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/my", tags=["my"])


@router.get("/equipment")
def my_equipment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MyEquipmentQueryHandler(asset_repo=AssetRepository(db))
    assets = handler.handle(
        MyEquipmentQuery(user_id=current_user.id, company_id=current_user.company_id)
    )
    return {
        "data": [
            MyEquipmentResponse(
                id=a.id,
                type=a.type.value,
                brand=a.brand,
                model=a.model,
                serial_number=a.serial_number,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in assets
        ]
    }


@router.get("/requests")
def my_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MyRequestsQueryHandler(request_repo=RequestRepository(db))
    requests, total = handler.handle(
        MyRequestsQuery(
            user_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=status,
        )
    )
    return {
        "data": [
            MyRequestResponse(
                id=r.id,
                type=r.type.value,
                title=r.title,
                status=r.status.value,
                priority=r.priority.value,
                assigned_to=r.assigned_to,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ).model_dump(mode="json")
            for r in requests
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }
