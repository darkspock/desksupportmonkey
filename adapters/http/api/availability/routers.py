import logging
from datetime import date

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.appointments.dependencies import (
    get_appointment_repo,
)
from adapters.http.api.availability.dependencies import (
    get_availability_repo,
    get_override_repo,
)
from adapters.http.api.availability.schemas import (
    AvailabilityWindowResponse,
    AvailabilityWindowSchema,
    OverrideCreateRequest,
    OverrideResponse,
    SetAvailabilityRequest,
    SlotResponse,
    SlotsQueryResponse,
)
from adapters.http.api.auth.dependencies import (
    get_current_user,
    require_role,
)
from core.database import get_db
from src.appointment_bc.appointment.application.commands.add_override import (
    AddOverrideCommand,
    AddOverrideCommandHandler,
)
from src.appointment_bc.appointment.application.commands.delete_override import (
    DeleteOverrideCommand,
    DeleteOverrideCommandHandler,
    OverrideNotFoundError,
)
from src.appointment_bc.appointment.application.commands.set_availability import (
    AvailabilityWindowInput,
    SetAvailabilityCommand,
    SetAvailabilityCommandHandler,
)
from src.appointment_bc.appointment.application.queries.get_availability import (
    GetAvailabilityQuery,
    GetAvailabilityQueryHandler,
)
from src.appointment_bc.appointment.application.queries.get_available_slots import (
    GetAvailableSlotsQuery,
    GetAvailableSlotsQueryHandler,
)
from src.appointment_bc.appointment.application.queries.list_overrides import (
    ListOverridesQuery,
    ListOverridesQueryHandler,
)
from src.appointment_bc.appointment.domain.entities import (
    AvailabilityOverride,
    TechnicianAvailability,
)
from src.appointment_bc.appointment.infrastructure.repository import (
    AppointmentRepository,
    AvailabilityOverrideRepository,
    TechnicianAvailabilityRepository,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/availability", tags=["availability"],
)


def _check_self_or_admin(
    current_user: User, technician_id: str,
) -> None:
    if current_user.role.has_access(UserRole.ADMIN):
        return
    if current_user.id != technician_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot manage another technician's availability",
        )


def _window_response(
    w: TechnicianAvailability,
) -> dict:
    return AvailabilityWindowResponse(
        id=w.id,
        day_of_week=w.day_of_week,
        start_time=w.start_time,
        end_time=w.end_time,
    ).model_dump(mode="json")


def _override_response(
    o: AvailabilityOverride,
) -> dict:
    return OverrideResponse(
        id=o.id,
        date=o.date,
        is_available=o.is_available,
        start_time=o.start_time,
        end_time=o.end_time,
        reason=o.reason,
        created_at=o.created_at,
        updated_at=o.updated_at,
    ).model_dump(mode="json")


@router.put("/technicians/{technician_id}")
def set_availability(
    technician_id: str,
    body: SetAvailabilityRequest,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    availability_repo: TechnicianAvailabilityRepository = Depends(
        get_availability_repo,
    ),
):
    _check_self_or_admin(current_user, technician_id)

    handler = SetAvailabilityCommandHandler(
        availability_repo=availability_repo,
    )
    try:
        handler.handle(
            SetAvailabilityCommand(
                technician_id=technician_id,
                company_id=current_user.company_id,
                windows=[
                    AvailabilityWindowInput(
                        day_of_week=w.day_of_week,
                        start_time=w.start_time,
                        end_time=w.end_time,
                    )
                    for w in body.windows
                ],
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    windows = availability_repo.find_by_technician(
        technician_id, current_user.company_id,
    )
    return {"data": [_window_response(w) for w in windows]}


@router.get("/technicians/{technician_id}")
def get_availability(
    technician_id: str,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    availability_repo: TechnicianAvailabilityRepository = Depends(
        get_availability_repo,
    ),
):
    _check_self_or_admin(current_user, technician_id)

    handler = GetAvailabilityQueryHandler(
        availability_repo=availability_repo,
    )
    windows = handler.handle(
        GetAvailabilityQuery(
            technician_id=technician_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": [_window_response(w) for w in windows]}


@router.post(
    "/technicians/{technician_id}/overrides",
    status_code=status.HTTP_201_CREATED,
)
def add_override(
    technician_id: str,
    body: OverrideCreateRequest,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    override_repo: AvailabilityOverrideRepository = Depends(
        get_override_repo,
    ),
):
    _check_self_or_admin(current_user, technician_id)

    override_id = ulid.new().str
    handler = AddOverrideCommandHandler(
        override_repo=override_repo,
    )
    try:
        handler.handle(
            AddOverrideCommand(
                override_id=override_id,
                company_id=current_user.company_id,
                technician_id=technician_id,
                target_date=body.date,
                is_available=body.is_available,
                start_time=body.start_time,
                end_time=body.end_time,
                reason=body.reason,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    override = override_repo.find_by_id(
        override_id, current_user.company_id,
    )
    return {"data": _override_response(override)}


@router.get("/technicians/{technician_id}/overrides")
def list_overrides(
    technician_id: str,
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    override_repo: AvailabilityOverrideRepository = Depends(
        get_override_repo,
    ),
):
    _check_self_or_admin(current_user, technician_id)

    handler = ListOverridesQueryHandler(
        override_repo=override_repo,
    )
    overrides = handler.handle(
        ListOverridesQuery(
            technician_id=technician_id,
            company_id=current_user.company_id,
            date_from=date_from,
            date_to=date_to,
        )
    )
    return {"data": [_override_response(o) for o in overrides]}


@router.delete("/overrides/{override_id}")
def delete_override(
    override_id: str,
    current_user: User = Depends(
        require_role(UserRole.TECHNICIAN),
    ),
    override_repo: AvailabilityOverrideRepository = Depends(
        get_override_repo,
    ),
):
    handler = DeleteOverrideCommandHandler(
        override_repo=override_repo,
    )
    try:
        handler.handle(
            DeleteOverrideCommand(
                override_id=override_id,
                company_id=current_user.company_id,
            )
        )
    except OverrideNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Override not found",
        )

    return {"data": {"deleted": True}}


@router.get("/technicians/{technician_id}/slots")
def get_available_slots(
    technician_id: str,
    target_date: date = Query(..., alias="date"),
    duration_minutes: int = Query(60, ge=30, le=90),
    current_user: User = Depends(get_current_user),
    availability_repo: TechnicianAvailabilityRepository = Depends(
        get_availability_repo,
    ),
    override_repo: AvailabilityOverrideRepository = Depends(
        get_override_repo,
    ),
    appointment_repo: AppointmentRepository = Depends(
        get_appointment_repo,
    ),
):
    handler = GetAvailableSlotsQueryHandler(
        availability_repo=availability_repo,
        override_repo=override_repo,
        appointment_repo=appointment_repo,
    )
    slots = handler.handle(
        GetAvailableSlotsQuery(
            technician_id=technician_id,
            company_id=current_user.company_id,
            target_date=target_date,
            duration_minutes=duration_minutes,
        )
    )

    return {
        "data": SlotsQueryResponse(
            date=target_date,
            technician_id=technician_id,
            duration_minutes=duration_minutes,
            slots=[
                SlotResponse(start=s.start, end=s.end)
                for s in slots
            ],
        ).model_dump(mode="json"),
    }
