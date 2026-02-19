from dataclasses import dataclass

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.repository import (
    AppointmentRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


class AppointmentNotFoundError(Exception):
    pass


@dataclass
class GetAppointmentQuery(Query):
    appointment_id: str
    company_id: str


class GetAppointmentQueryHandler(
    QueryHandler[GetAppointmentQuery, Appointment],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, query: GetAppointmentQuery,
    ) -> Appointment:
        appointment = self.appointment_repo.find_by_id(
            query.appointment_id, query.company_id,
        )
        if not appointment:
            raise AppointmentNotFoundError(
                f"Appointment {query.appointment_id} "
                f"not found"
            )
        return appointment
