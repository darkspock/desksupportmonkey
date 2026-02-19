from datetime import date, time
from unittest.mock import MagicMock, patch

from src.appointment_bc.appointment.application.queries.get_availability import (
    GetAvailabilityQuery,
    GetAvailabilityQueryHandler,
)
from src.appointment_bc.appointment.application.queries.list_overrides import (
    ListOverridesQuery,
    ListOverridesQueryHandler,
)
from src.appointment_bc.appointment.application.queries.get_available_slots import (
    GetAvailableSlotsQuery,
    GetAvailableSlotsQueryHandler,
)
from src.appointment_bc.appointment.domain.services import TimeSlot


class TestGetAvailability:

    def test_get_availability_returns_windows(self):
        window = MagicMock()
        repo = MagicMock()
        repo.find_by_technician.return_value = [window]

        handler = GetAvailabilityQueryHandler(
            availability_repo=repo,
        )
        result = handler.handle(
            GetAvailabilityQuery(
                technician_id="tech1",
                company_id="comp1",
            )
        )
        assert len(result) == 1
        assert result[0] is window
        repo.find_by_technician.assert_called_once_with(
            "tech1", "comp1",
        )


class TestListOverrides:

    def test_list_overrides_returns_filtered(self):
        override = MagicMock()
        repo = MagicMock()
        repo.find_by_technician_date_range.return_value = [
            override,
        ]

        handler = ListOverridesQueryHandler(
            override_repo=repo,
        )
        result = handler.handle(
            ListOverridesQuery(
                technician_id="tech1",
                company_id="comp1",
                date_from=date(2026, 3, 1),
                date_to=date(2026, 3, 31),
            )
        )
        assert len(result) == 1
        repo.find_by_technician_date_range.assert_called_once()


class TestGetAvailableSlots:

    def test_get_available_slots_integrates_service(self):
        avail_repo = MagicMock()
        avail_repo.find_by_technician_day.return_value = []
        override_repo = MagicMock()
        override_repo.find_by_technician_date.return_value = []
        appt_repo = MagicMock()
        appt_repo.find_by_technician_date_range.return_value = []

        handler = GetAvailableSlotsQueryHandler(
            availability_repo=avail_repo,
            override_repo=override_repo,
            appointment_repo=appt_repo,
        )

        # Monday, March 2, 2026 — uses default weekday windows
        result = handler.handle(
            GetAvailableSlotsQuery(
                technician_id="tech1",
                company_id="comp1",
                target_date=date(2026, 3, 2),
                duration_minutes=60,
            )
        )

        # Default weekday: 9-12, 14-17 → 6 one-hour slots
        assert len(result) == 6
        avail_repo.find_by_technician_day.assert_called_once()
        override_repo.find_by_technician_date.assert_called_once()
        appt_repo.find_by_technician_date_range.assert_called_once()
