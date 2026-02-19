from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import List

from src.appointment_bc.appointment.domain.repository import (
    AppointmentRepositoryInterface,
    AvailabilityOverrideRepositoryInterface,
    TechnicianAvailabilityRepositoryInterface,
)
from src.appointment_bc.appointment.domain.services import (
    AvailabilityService,
    TimeSlot,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


@dataclass
class GetAvailableSlotsQuery(Query):
    technician_id: str
    company_id: str
    target_date: date
    duration_minutes: int


class GetAvailableSlotsQueryHandler(
    QueryHandler[
        GetAvailableSlotsQuery,
        List[TimeSlot],
    ],
):
    def __init__(
        self,
        availability_repo: TechnicianAvailabilityRepositoryInterface,
        override_repo: AvailabilityOverrideRepositoryInterface,
        appointment_repo: AppointmentRepositoryInterface,
    ):
        self.availability_repo = availability_repo
        self.override_repo = override_repo
        self.appointment_repo = appointment_repo

    def handle(
        self, query: GetAvailableSlotsQuery,
    ) -> List[TimeSlot]:
        recurring = self.availability_repo.find_by_technician_day(
            technician_id=query.technician_id,
            company_id=query.company_id,
            day_of_week=query.target_date.weekday(),
        )

        overrides = self.override_repo.find_by_technician_date(
            technician_id=query.technician_id,
            company_id=query.company_id,
            target_date=query.target_date,
        )

        day_start = datetime.combine(
            query.target_date,
            time(0, 0),
            tzinfo=timezone.utc,
        )
        day_end = datetime.combine(
            query.target_date,
            time(23, 59, 59),
            tzinfo=timezone.utc,
        )
        appointments = (
            self.appointment_repo.find_by_technician_date_range(
                technician_id=query.technician_id,
                company_id=query.company_id,
                start=day_start,
                end=day_end,
            )
        )

        return AvailabilityService.compute_available_slots(
            target_date=query.target_date,
            duration_minutes=query.duration_minutes,
            recurring_windows=recurring,
            overrides=overrides,
            existing_appointments=appointments,
        )
