import logging
from datetime import datetime
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.appointments.dependencies import (
    get_appointment_repo,
)
from adapters.http.api.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentResponse,
    CancelAppointmentRequest,
    CompleteAppointmentRequest,
    RescheduleAppointmentRequest,
)
from adapters.http.api.auth.dependencies import (
    get_current_user,
    require_role,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.appointment_bc.appointment.application.commands.cancel_appointment import (
    CancelAppointmentCommand,
    CancelAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.cancel_appointment import (
    AppointmentNotFoundError as CancelNotFoundError,
)
from src.appointment_bc.appointment.application.commands.complete_appointment import (
    CompleteAppointmentCommand,
    CompleteAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.complete_appointment import (
    AppointmentNotFoundError as CompleteNotFoundError,
)
from src.appointment_bc.appointment.application.commands.confirm_appointment import (
    ConfirmAppointmentCommand,
    ConfirmAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.confirm_appointment import (
    AppointmentNotFoundError as ConfirmNotFoundError,
)
from src.appointment_bc.appointment.application.commands.create_appointment import (
    AppointmentOverlapError,
    CreateAppointmentCommand,
    CreateAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.reschedule_appointment import (
    RescheduleAppointmentCommand,
    RescheduleAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.reschedule_appointment import (
    AppointmentNotFoundError as RescheduleNotFoundError,
)
from src.appointment_bc.appointment.application.queries.get_appointment import (
    AppointmentNotFoundError as GetNotFoundError,
    GetAppointmentQuery,
    GetAppointmentQueryHandler,
)
from src.appointment_bc.appointment.application.queries.list_appointments import (
    ListAppointmentsQuery,
    ListAppointmentsQueryHandler,
)
from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.enums import (
    InvalidAppointmentStatusTransitionError,
)
from src.appointment_bc.appointment.infrastructure.repository import (
    AppointmentRepository,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.notification_bc.notification.application.services.appointment_event_factory import (
    AppointmentEventFactory,
)
from src.notification_bc.notification.application.services.event_bus import (
    EventBus,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/appointments", tags=["appointments"],
)


def _to_response(
    appointment: Appointment,
    technician_email: Optional[str] = None,
    employee_email: Optional[str] = None,
) -> dict:
    return AppointmentResponse(
        id=appointment.id,
        company_id=appointment.company_id,
        request_id=appointment.request_id,
        technician_id=appointment.technician_id,
        employee_id=appointment.employee_id,
        status=appointment.status.value,
        scheduled_start=appointment.scheduled_start,
        scheduled_end=appointment.scheduled_end,
        duration_minutes=appointment.duration_minutes,
        location=appointment.location,
        notes=appointment.notes,
        cancellation_reason=appointment.cancellation_reason,
        cancelled_by=appointment.cancelled_by,
        rescheduled_from_id=appointment.rescheduled_from_id,
        completed_at=appointment.completed_at,
        created_by=appointment.created_by,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        technician_email=technician_email,
        employee_email=employee_email,
    ).model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(
    body: AppointmentCreateRequest,
    current_user: User = Depends(get_current_user),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    appointment_id = ulid.new().str
    handler = CreateAppointmentCommandHandler(
        appointment_repo=appointment_repo,
    )
    try:
        handler.handle(
            CreateAppointmentCommand(
                appointment_id=appointment_id,
                company_id=current_user.company_id,
                request_id=body.request_id,
                technician_id=body.technician_id,
                employee_id=body.employee_id,
                scheduled_start=body.scheduled_start,
                duration_minutes=body.duration_minutes,
                created_by=current_user.id,
                creator_role=current_user.role.value,
                location=body.location,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except AppointmentOverlapError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    appointment = appointment_repo.find_by_id(
        appointment_id, current_user.company_id,
    )
    event = AppointmentEventFactory.appointment_created(
        appointment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(appointment)}


@router.get("")
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    appointment_status: Optional[str] = Query(
        None, alias="status",
    ),
    technician_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    request_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
):
    handler = ListAppointmentsQueryHandler(
        appointment_repo=appointment_repo,
    )
    appointments, total = handler.handle(
        ListAppointmentsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=appointment_status,
            technician_id=technician_id,
            employee_id=employee_id,
            request_id=request_id,
            date_from=date_from,
            date_to=date_to,
        )
    )
    return {
        "data": [_to_response(a) for a in appointments],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
):
    handler = GetAppointmentQueryHandler(
        appointment_repo=appointment_repo,
    )
    try:
        appointment = handler.handle(
            GetAppointmentQuery(
                appointment_id=appointment_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Access control: employees can only see their own
    if not current_user.role.has_access(UserRole.TECHNICIAN):
        if appointment.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found",
            )

    return {"data": _to_response(appointment)}


@router.post("/{appointment_id}/confirm")
def confirm_appointment(
    appointment_id: str,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = ConfirmAppointmentCommandHandler(
        appointment_repo=appointment_repo,
    )
    try:
        handler.handle(
            ConfirmAppointmentCommand(
                appointment_id=appointment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ConfirmNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    except InvalidAppointmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    appointment = appointment_repo.find_by_id(
        appointment_id, current_user.company_id,
    )
    event = AppointmentEventFactory.appointment_confirmed(
        appointment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(appointment)}


@router.post("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: str,
    body: CancelAppointmentRequest,
    current_user: User = Depends(get_current_user),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = CancelAppointmentCommandHandler(
        appointment_repo=appointment_repo,
    )
    try:
        handler.handle(
            CancelAppointmentCommand(
                appointment_id=appointment_id,
                company_id=current_user.company_id,
                reason=body.reason,
                performed_by=current_user.id,
            )
        )
    except CancelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    except InvalidAppointmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    appointment = appointment_repo.find_by_id(
        appointment_id, current_user.company_id,
    )
    event = AppointmentEventFactory.appointment_cancelled(
        appointment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(appointment)}


@router.post("/{appointment_id}/complete")
def complete_appointment(
    appointment_id: str,
    body: CompleteAppointmentRequest,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = CompleteAppointmentCommandHandler(
        appointment_repo=appointment_repo,
    )
    try:
        handler.handle(
            CompleteAppointmentCommand(
                appointment_id=appointment_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                notes=body.notes,
            )
        )
    except CompleteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    except InvalidAppointmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    appointment = appointment_repo.find_by_id(
        appointment_id, current_user.company_id,
    )
    event = AppointmentEventFactory.appointment_completed(
        appointment, actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(appointment)}


@router.post(
    "/{appointment_id}/reschedule",
    status_code=status.HTTP_201_CREATED,
)
def reschedule_appointment(
    appointment_id: str,
    body: RescheduleAppointmentRequest,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    new_appointment_id = ulid.new().str
    handler = RescheduleAppointmentCommandHandler(
        appointment_repo=appointment_repo,
    )
    try:
        handler.handle(
            RescheduleAppointmentCommand(
                new_appointment_id=new_appointment_id,
                appointment_id=appointment_id,
                company_id=current_user.company_id,
                new_start=body.new_start,
                new_duration_minutes=body.new_duration_minutes,
                performed_by=current_user.id,
                creator_role=current_user.role.value,
                reason=body.reason,
                location=body.location,
            )
        )
    except RescheduleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    except InvalidAppointmentStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except AppointmentOverlapError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    old_appointment = appointment_repo.find_by_id(
        appointment_id, current_user.company_id,
    )
    new_appointment = appointment_repo.find_by_id(
        new_appointment_id, current_user.company_id,
    )
    event = AppointmentEventFactory.appointment_rescheduled(
        old_appointment,
        new_appointment,
        actor_id=current_user.id,
    )
    event_bus.publish(event, db)

    return {"data": _to_response(new_appointment)}
