from dataclasses import dataclass

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
class ConfirmAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    performed_by: str


class ConfirmAppointmentCommandHandler(
    CommandHandler[ConfirmAppointmentCommand],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, command: ConfirmAppointmentCommand,
    ) -> None:
        appointment = self.appointment_repo.find_by_id(
            command.appointment_id, command.company_id,
        )
        if not appointment:
            raise AppointmentNotFoundError(
                f"Appointment {command.appointment_id} "
                f"not found"
            )
        appointment.confirm()
        self.appointment_repo.save(appointment)
