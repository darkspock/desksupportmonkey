import logging

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import get_current_user, require_role
from adapters.http.api.my.dependencies import (
    get_appointment_repo,
    get_asset_repo,
    get_company_repo,
    get_maintenance_record_repo,
    get_notification_repo,
    get_request_repo,
    get_shipment_repo,
    get_user_repo,
)
from adapters.http.api.my.schemas import (
    MyEquipmentResponse,
    MyCompanySettingsResponse,
    MyMaintenanceResponse,
    MyRequestResponse,
    NotificationListMeta,
    NotificationResponse,
    UpdateMyCompanySettingsRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.company_bc.company.application.commands.update_company import (
    CompanyNotFoundError as UpdateCompanyNotFoundError,
)
from src.company_bc.company.application.commands.update_company import (
    DomainAlreadyTakenError as UpdateDomainTakenError,
)
from src.company_bc.company.application.commands.update_company import (
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.application.queries.get_company import (
    CompanyNotFoundError as GetCompanyNotFoundError,
)
from src.company_bc.company.application.queries.get_company import (
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.infrastructure.repository import CompanyRepository
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
from src.appointment_bc.appointment.application.queries.my_appointments import (
    MyAppointmentsQuery,
    MyAppointmentsQueryHandler,
)
from src.appointment_bc.appointment.infrastructure.repository import (
    AppointmentRepository,
)
from src.shipping_bc.shipment.application.queries.my_shipments import (
    MyShipmentsQuery,
    MyShipmentsQueryHandler,
)
from src.shipping_bc.shipment.infrastructure.repository import (
    ShipmentRepository,
)
from src.maintenance_bc.maintenance_record.application.queries.my_maintenance import (
    MyMaintenanceQuery,
    MyMaintenanceQueryHandler,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/my", tags=["my"])


def _validate_admin_with_company(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only company admins can access company settings",
        )
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Current user has no company assigned",
        )


def _to_company_settings(detail: object) -> dict:
    return {
        "data": MyCompanySettingsResponse(
            id=detail.company.id,
            name=detail.company.name,
            email_domains=detail.company.email_domains,
        ).model_dump(mode="json")
    }


@router.get("/equipment")
def my_equipment(
    current_user: User = Depends(get_current_user),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    handler = MyEquipmentQueryHandler(asset_repo=asset_repo)
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


def _to_my_request(r: object, user_map: dict) -> dict:
    return MyRequestResponse(
        id=r.id, type=r.type.value, subtype=r.subtype, title=r.title, status=r.status.value,
        priority=r.priority.value, assigned_to=r.assigned_to,
        assigned_to_email=user_map[r.assigned_to].email if r.assigned_to and r.assigned_to in user_map else None,
        created_at=r.created_at, updated_at=r.updated_at,
    ).model_dump(mode="json")


@router.get("/requests")
def my_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    subtype: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = MyRequestsQueryHandler(request_repo=request_repo)
    requests, total = handler.handle(
        MyRequestsQuery(
            user_id=current_user.id, company_id=current_user.company_id,
            page=page, page_size=page_size, status=status, subtype=subtype,
        )
    )
    user_map = user_repo.find_by_ids([r.assigned_to for r in requests if r.assigned_to])
    return {
        "data": [_to_my_request(r, user_map) for r in requests],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


def _to_notification(n: object) -> dict:
    return NotificationResponse(
        id=n.id, event_type=n.event_type, title=n.title, body=n.body,
        data=n.data, is_read=n.is_read, created_at=n.created_at,
    ).model_dump(mode="json")


@router.get("/notifications")
def my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    notification_repo: NotificationRepository = Depends(get_notification_repo),
):
    handler = ListNotificationsQueryHandler(notification_repo=notification_repo)
    notifications, total, unread_count = handler.handle(
        ListNotificationsQuery(user_id=current_user.id, page=page, page_size=page_size, is_read=is_read)
    )
    return {
        "data": [_to_notification(n) for n in notifications],
        "meta": NotificationListMeta(page=page, page_size=page_size, total=total, unread_count=unread_count).model_dump(),
    }


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    notification_repo: NotificationRepository = Depends(get_notification_repo),
):
    handler = MarkReadCommandHandler(notification_repo=notification_repo)
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
    notification_repo: NotificationRepository = Depends(get_notification_repo),
):
    handler = MarkAllReadCommandHandler(notification_repo=notification_repo)
    handler.handle(MarkAllReadCommand(user_id=current_user.id))
    return {"data": {"success": True}}


@router.get("/company-settings")
def get_my_company_settings(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    _validate_admin_with_company(current_user)

    handler = GetCompanyQueryHandler(company_repo=company_repo)
    try:
        detail = handler.handle(GetCompanyQuery(company_id=current_user.company_id))
    except GetCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    return _to_company_settings(detail)


@router.put("/company-settings")
def update_my_company_settings(
    body: UpdateMyCompanySettingsRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    _validate_admin_with_company(current_user)

    handler = UpdateCompanyCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanyCommand(
                company_id=current_user.company_id,
                email_domains=body.email_domains,
            )
        )
    except UpdateCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except UpdateDomainTakenError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    query_handler = GetCompanyQueryHandler(company_repo=company_repo)
    detail = query_handler.handle(GetCompanyQuery(company_id=current_user.company_id))

    return _to_company_settings(detail)


@router.get("/appointments")
def my_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    appointment_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    appointment_repo: AppointmentRepository = Depends(get_appointment_repo),
):
    handler = MyAppointmentsQueryHandler(appointment_repo=appointment_repo)
    appointments, total = handler.handle(
        MyAppointmentsQuery(
            employee_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=appointment_status,
        )
    )
    return {
        "data": [
            {
                "id": a.id,
                "request_id": a.request_id,
                "technician_id": a.technician_id,
                "status": a.status.value,
                "scheduled_start": a.scheduled_start.isoformat() if a.scheduled_start else None,
                "scheduled_end": a.scheduled_end.isoformat() if a.scheduled_end else None,
                "duration_minutes": a.duration_minutes,
                "location": a.location,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in appointments
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/shipments")
def my_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    shipment_repo: ShipmentRepository = Depends(get_shipment_repo),
):
    handler = MyShipmentsQueryHandler(shipment_repo=shipment_repo)
    shipments, total = handler.handle(
        MyShipmentsQuery(
            recipient_user_id=current_user.id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [
            {
                "id": s.id,
                "direction": s.direction.value,
                "destination_type": s.destination_type.value,
                "status": s.status.value,
                "carrier": s.carrier,
                "tracking_number": s.tracking_number,
                "tracking_url": s.tracking_url,
                "dispatched_at": s.dispatched_at.isoformat() if s.dispatched_at else None,
                "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
                "item_count": len(s.items),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in shipments
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/maintenance")
def my_maintenance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    record_repo: MaintenanceRecordRepository = Depends(
        get_maintenance_record_repo,
    ),
):
    handler = MyMaintenanceQueryHandler(
        record_repo=record_repo,
    )
    records, total = handler.handle(
        MyMaintenanceQuery(
            company_id=current_user.company_id,
            technician_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [
            MyMaintenanceResponse(
                id=r.id,
                asset_id=r.asset_id,
                status=r.status.value,
                priority=r.priority.value,
                title=r.title,
                scheduled_at=r.scheduled_at,
                started_at=r.started_at,
                completed_at=r.completed_at,
            ).model_dump(mode="json")
            for r in records
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }
