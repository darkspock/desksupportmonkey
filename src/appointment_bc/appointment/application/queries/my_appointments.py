from dataclasses import dataclass
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
class MyAppointmentsQuery(Query):
    employee_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None


class MyAppointmentsQueryHandler(
    QueryHandler[
        MyAppointmentsQuery,
        tuple[list[Appointment], int],
    ],
):
    def __init__(
        self,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.appointment_repo = appointment_repo

    def handle(
        self, query: MyAppointmentsQuery,
    ) -> tuple[list[Appointment], int]:
        return self.appointment_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            employee_id=query.employee_id,
        )
