from dataclasses import dataclass
from typing import Optional

from src.appointment_bc.appointment.domain.repository import (
    AppointmentRepositoryInterface,
)
from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)


class AppointmentNotFoundError(Exception):
    pass


@dataclass
class CompleteAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    performed_by: str
    notes: Optional[str] = None


class CompleteAppointmentCommandHandler(
    CommandHandler[CompleteAppointmentCommand],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, command: CompleteAppointmentCommand,
    ) -> None:
        appointment = self.appointment_repo.find_by_id(
            command.appointment_id, command.company_id,
        )
        if not appointment:
            raise AppointmentNotFoundError(
                f"Appointment {command.appointment_id} "
                f"not found"
            )
        appointment.complete(notes=command.notes)
        self.appointment_repo.save(appointment)
