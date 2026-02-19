from dataclasses import dataclass
from typing import List

from src.appointment_bc.appointment.domain.entities import (
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.repository import (
    TechnicianAvailabilityRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class GetAvailabilityQuery(Query):
    technician_id: str
    company_id: str


class GetAvailabilityQueryHandler(
    QueryHandler[
        GetAvailabilityQuery,
        List[TechnicianAvailability],
    ],
):
    def __init__(
        self,
        availability_repo: TechnicianAvailabilityRepositoryInterface,
    ):
        self.availability_repo = availability_repo

    def handle(
        self, query: GetAvailabilityQuery,
    ) -> List[TechnicianAvailability]:
        return self.availability_repo.find_by_technician(
            query.technician_id, query.company_id,
        )
