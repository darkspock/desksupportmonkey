import logging

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.my.schemas import (
    MyEquipmentResponse,
    MyRequestResponse,
    NotificationListMeta,
    NotificationResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.notification_bc.notification.application.commands.mark_all_read import (
    MarkAllReadCommand,
    MarkAllReadCommandHandler,
)
from src.notification_bc.notification.application.commands.mark_read import (
    MarkReadCommand,
    MarkReadCommandHandler,
    NotificationNotFoundError,
)
from src.notification_bc.notification.application.queries.list_notifications import (
    ListNotificationsQuery,
    ListNotificationsQueryHandler,
)
from src.notification_bc.notification.infrastructure.repository import NotificationRepository
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


@router.get("/notifications")
def my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = ListNotificationsQueryHandler(
        notification_repo=NotificationRepository(db)
    )
    notifications, total, unread_count = handler.handle(
        ListNotificationsQuery(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            is_read=is_read,
        )
    )
    return {
        "data": [
            NotificationResponse(
                id=n.id,
                event_type=n.event_type,
                title=n.title,
                body=n.body,
                data=n.data,
                is_read=n.is_read,
                created_at=n.created_at,
            ).model_dump(mode="json")
            for n in notifications
        ],
        "meta": NotificationListMeta(
            page=page, page_size=page_size, total=total, unread_count=unread_count
        ).model_dump(),
    }


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MarkReadCommandHandler(notification_repo=NotificationRepository(db))
    try:
        handler.handle(
            MarkReadCommand(notification_id=notification_id, user_id=current_user.id)
        )
    except NotificationNotFoundError:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"data": {"id": notification_id, "is_read": True}}


@router.patch("/notifications/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handler = MarkAllReadCommandHandler(notification_repo=NotificationRepository(db))
    marked_count = handler.handle(MarkAllReadCommand(user_id=current_user.id))
    return {"data": {"marked_count": marked_count}}
