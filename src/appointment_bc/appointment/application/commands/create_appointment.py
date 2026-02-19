import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)
from src.appointment_bc.appointment.domain.repository import (
    AppointmentRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class AppointmentOverlapError(Exception):
    pass


@dataclass
class CreateAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    scheduled_start: datetime
    duration_minutes: int
    created_by: str
    creator_role: str
    location: Optional[str] = None
    rescheduled_from_id: Optional[str] = None


class CreateAppointmentCommandHandler(
    CommandHandler[CreateAppointmentCommand],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, command: CreateAppointmentCommand,
    ) -> None:
        if command.creator_role in (
            "technician", "admin", "super_admin",
        ):
            initial_status = AppointmentStatus.CONFIRMED
        else:
            initial_status = AppointmentStatus.PENDING

        appointment = Appointment.create(
            company_id=command.company_id,
            request_id=command.request_id,
            technician_id=command.technician_id,
            employee_id=command.employee_id,
            scheduled_start=command.scheduled_start,
            duration_minutes=command.duration_minutes,
            created_by=command.created_by,
            initial_status=initial_status,
            location=command.location,
            rescheduled_from_id=command.rescheduled_from_id,
            id=command.appointment_id,
        )

        # Check technician overlap
        tech_overlaps = (
            self.appointment_repo
            .find_by_technician_date_range(
                technician_id=command.technician_id,
                company_id=command.company_id,
                start=appointment.scheduled_start,
                end=appointment.scheduled_end,
            )
        )
        if tech_overlaps:
            raise AppointmentOverlapError(
                "Technician already has a confirmed "
                "appointment in this time range"
            )

        # Check employee overlap
        emp_overlaps = (
            self.appointment_repo
            .find_by_employee_date_range(
                employee_id=command.employee_id,
                company_id=command.company_id,
                start=appointment.scheduled_start,
                end=appointment.scheduled_end,
            )
        )
        if emp_overlaps:
            raise AppointmentOverlapError(
                "Employee already has a confirmed "
                "appointment in this time range"
            )

        self.appointment_repo.save(appointment)

        logger.info(
            "Appointment %s created for request %s",
            appointment.id,
            command.request_id,
        )
