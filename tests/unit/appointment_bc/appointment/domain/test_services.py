from datetime import date, datetime, time, UTC

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
    AvailabilityOverride,
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)
from src.appointment_bc.appointment.domain.services import (
    AvailabilityService,
    TimeSlot,
)


def _make_availability(
    day: int,
    start: time,
    end: time,
) -> TechnicianAvailability:
    return TechnicianAvailability.create(
        company_id="comp1",
        technician_id="tech1",
        day_of_week=day,
        start_time=start,
        end_time=end,
    )


def _make_override(
    target_date: date,
    is_available: bool,
    start: time | None = None,
    end: time | None = None,
) -> AvailabilityOverride:
    return AvailabilityOverride.create(
        company_id="comp1",
        technician_id="tech1",
        target_date=target_date,
        is_available=is_available,
        start_time=start,
        end_time=end,
    )


def _make_appointment(
    start: datetime,
    duration: int = 60,
) -> Appointment:
    return Appointment.create(
        company_id="comp1",
        request_id="req1",
        technician_id="tech1",
        employee_id="emp1",
        scheduled_start=start,
        duration_minutes=duration,
        created_by="tech1",
        initial_status=AppointmentStatus.CONFIRMED,
    )


class TestComputeAvailableSlots:

    def test_simple_recurring_window(self):
        # Wednesday 2026-03-04 → weekday=2 (Wednesday)
        target = date(2026, 3, 4)
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[],
        )
        assert len(slots) == 3
        assert slots[0] == TimeSlot(
            time(9, 0), time(10, 0),
        )
        assert slots[1] == TimeSlot(
            time(10, 0), time(11, 0),
        )
        assert slots[2] == TimeSlot(
            time(11, 0), time(12, 0),
        )

    def test_multiple_windows(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
            _make_availability(
                2, time(14, 0), time(17, 0),
            ),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[],
        )
        assert len(slots) == 6

    def test_30_min_slots(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=30,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[],
        )
        assert len(slots) == 6

    def test_90_min_slots(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=90,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[],
        )
        assert len(slots) == 2
        assert slots[0] == TimeSlot(
            time(9, 0), time(10, 30),
        )
        assert slots[1] == TimeSlot(
            time(10, 30), time(12, 0),
        )

    def test_blocked_override_removes_entire_day(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(17, 0)),
        ]
        overrides = [
            _make_override(target, is_available=False),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=overrides,
            existing_appointments=[],
        )
        assert len(slots) == 0

    def test_blocked_override_with_range(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        overrides = [
            _make_override(
                target,
                is_available=False,
                start=time(10, 0),
                end=time(11, 0),
            ),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=overrides,
            existing_appointments=[],
        )
        # 09:00-10:00 and 11:00-12:00
        assert len(slots) == 2
        assert slots[0] == TimeSlot(
            time(9, 0), time(10, 0),
        )
        assert slots[1] == TimeSlot(
            time(11, 0), time(12, 0),
        )

    def test_extra_override_adds_window(self):
        # Saturday 2026-03-07 → weekday=5
        target = date(2026, 3, 7)
        overrides = [
            _make_override(
                target,
                is_available=True,
                start=time(10, 0),
                end=time(14, 0),
            ),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=[],
            overrides=overrides,
            existing_appointments=[],
        )
        assert len(slots) == 4

    def test_subtract_existing_appointment(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        appt = _make_appointment(
            datetime(2026, 3, 4, 10, 0, tzinfo=UTC),
            duration=60,
        )
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[appt],
        )
        # 09:00-10:00 and 11:00-12:00
        assert len(slots) == 2
        assert slots[0] == TimeSlot(
            time(9, 0), time(10, 0),
        )
        assert slots[1] == TimeSlot(
            time(11, 0), time(12, 0),
        )

    def test_default_weekday_availability(self):
        # Monday 2026-03-02 → weekday=0
        target = date(2026, 3, 2)
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=[],
            overrides=[],
            existing_appointments=[],
        )
        # Default: 09:00-12:00 (3 slots) + 14:00-17:00 (3)
        assert len(slots) == 6

    def test_default_weekend_no_availability(self):
        # Saturday 2026-03-07 → weekday=5
        target = date(2026, 3, 7)
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=[],
            overrides=[],
            existing_appointments=[],
        )
        assert len(slots) == 0

    def test_no_slots_when_fully_blocked(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        appointments = [
            _make_appointment(
                datetime(2026, 3, 4, 9, 0, tzinfo=UTC), 60,
            ),
            _make_appointment(
                datetime(2026, 3, 4, 10, 0, tzinfo=UTC), 60,
            ),
            _make_appointment(
                datetime(2026, 3, 4, 11, 0, tzinfo=UTC), 60,
            ),
        ]
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=60,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=appointments,
        )
        assert len(slots) == 0

    def test_partial_window_after_subtraction(self):
        target = date(2026, 3, 4)  # Wednesday
        windows = [
            _make_availability(2, time(9, 0), time(12, 0)),
        ]
        # Appointment 09:30-10:30 breaks the window
        appt = Appointment(
            id="appt1",
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            status=AppointmentStatus.CONFIRMED,
            scheduled_start=datetime(
                2026, 3, 4, 9, 30, tzinfo=UTC,
            ),
            scheduled_end=datetime(
                2026, 3, 4, 10, 30, tzinfo=UTC,
            ),
            duration_minutes=60,
            created_by="tech1",
        )
        slots = AvailabilityService.compute_available_slots(
            target_date=target,
            duration_minutes=30,
            recurring_windows=windows,
            overrides=[],
            existing_appointments=[appt],
        )
        # 09:00-09:30 (1 slot of 30min)
        # 10:30-12:00 (3 slots of 30min)
        assert len(slots) == 4
        assert slots[0] == TimeSlot(
            time(9, 0), time(9, 30),
        )
        assert slots[1] == TimeSlot(
            time(10, 30), time(11, 0),
        )
