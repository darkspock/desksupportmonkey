from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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


@dataclass
class ListAppointmentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    technician_id: Optional[str] = None
    employee_id: Optional[str] = None
    request_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ListAppointmentsQueryHandler(
    QueryHandler[
        ListAppointmentsQuery,
        tuple[list[Appointment], int],
    ],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, query: ListAppointmentsQuery,
    ) -> tuple[list[Appointment], int]:
        return self.appointment_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            technician_id=query.technician_id,
            employee_id=query.employee_id,
            request_id=query.request_id,
            date_from=query.date_from,
            date_to=query.date_to,
        )
