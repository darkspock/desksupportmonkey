from dataclasses import dataclass
from datetime import date
from typing import List

from src.appointment_bc.appointment.domain.entities import (
    AvailabilityOverride,
)
from src.appointment_bc.appointment.domain.repository import (
    AvailabilityOverrideRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class ListOverridesQuery(Query):
    technician_id: str
    company_id: str
    date_from: date
    date_to: date


class ListOverridesQueryHandler(
    QueryHandler[
        ListOverridesQuery,
        List[AvailabilityOverride],
    ],
):
    def __init__(
        self,
        override_repo: AvailabilityOverrideRepositoryInterface,
    ):
        self.override_repo = override_repo

    def handle(
        self, query: ListOverridesQuery,
    ) -> List[AvailabilityOverride]:
        return self.override_repo.find_by_technician_date_range(
            technician_id=query.technician_id,
            company_id=query.company_id,
            date_from=query.date_from,
            date_to=query.date_to,
        )
