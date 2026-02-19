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
from src.appointment_bc.appointment.application.commands.create_appointment import (
    AppointmentOverlapError,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)

logger = logging.getLogger(__name__)


class AppointmentNotFoundError(Exception):
    pass


@dataclass
class RescheduleAppointmentCommand(Command):
    new_appointment_id: str
    appointment_id: str
    company_id: str
    new_start: datetime
    new_duration_minutes: int
    performed_by: str
    creator_role: str
    reason: str
    location: Optional[str] = None


class RescheduleAppointmentCommandHandler(
    CommandHandler[RescheduleAppointmentCommand],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, command: RescheduleAppointmentCommand,
    ) -> None:
        old = self.appointment_repo.find_by_id(
            command.appointment_id, command.company_id,
        )
        if not old:
            raise AppointmentNotFoundError(
                f"Appointment {command.appointment_id} "
                f"not found"
            )

        # Cancel the old appointment
        old.cancel(
            reason=f"Rescheduled: {command.reason}",
            cancelled_by=command.performed_by,
        )
        self.appointment_repo.save(old)

        # Determine initial status for new appointment
        if command.creator_role in (
            "technician", "admin", "super_admin",
        ):
            initial_status = AppointmentStatus.CONFIRMED
        else:
            initial_status = AppointmentStatus.PENDING

        # Create the new appointment
        new_appointment = Appointment.create(
            company_id=old.company_id,
            request_id=old.request_id,
            technician_id=old.technician_id,
            employee_id=old.employee_id,
            scheduled_start=command.new_start,
            duration_minutes=command.new_duration_minutes,
            created_by=command.performed_by,
            initial_status=initial_status,
            location=command.location or old.location,
            rescheduled_from_id=old.id,
            id=command.new_appointment_id,
        )

        # Check technician overlap
        tech_overlaps = (
            self.appointment_repo
            .find_by_technician_date_range(
                technician_id=old.technician_id,
                company_id=command.company_id,
                start=new_appointment.scheduled_start,
                end=new_appointment.scheduled_end,
            )
        )
        if tech_overlaps:
            raise AppointmentOverlapError(
                "Technician already has a confirmed "
                "appointment in the new time range"
            )

        # Check employee overlap
        emp_overlaps = (
            self.appointment_repo
            .find_by_employee_date_range(
                employee_id=old.employee_id,
                company_id=command.company_id,
                start=new_appointment.scheduled_start,
                end=new_appointment.scheduled_end,
            )
        )
        if emp_overlaps:
            raise AppointmentOverlapError(
                "Employee already has a confirmed "
                "appointment in the new time range"
            )

        self.appointment_repo.save(new_appointment)

        logger.info(
            "Appointment %s rescheduled to %s",
            old.id,
            new_appointment.id,
        )
