from datetime import datetime, time, date, UTC

import pytest

from src.appointment_bc.appointment.domain.entities import (
    Appointment,
    AvailabilityOverride,
    TechnicianAvailability,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
    InvalidAppointmentStatusTransitionError,
)


class TestAppointmentCreate:

    def test_create_appointment_pending(self):
        appt = Appointment.create(
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            scheduled_start=datetime(
                2026, 3, 1, 10, 0, tzinfo=UTC,
            ),
            duration_minutes=60,
            created_by="emp1",
            initial_status=AppointmentStatus.PENDING,
        )
        assert appt.status == AppointmentStatus.PENDING
        assert appt.company_id == "comp1"
        assert appt.created_by == "emp1"
        assert appt.id is not None

    def test_create_appointment_confirmed(self):
        appt = Appointment.create(
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            scheduled_start=datetime(
                2026, 3, 1, 10, 0, tzinfo=UTC,
            ),
            duration_minutes=60,
            created_by="tech1",
            initial_status=AppointmentStatus.CONFIRMED,
        )
        assert appt.status == AppointmentStatus.CONFIRMED

    def test_create_validates_duration(self):
        with pytest.raises(ValueError, match="30, 60, 90"):
            Appointment.create(
                company_id="comp1",
                request_id="req1",
                technician_id="tech1",
                employee_id="emp1",
                scheduled_start=datetime(
                    2026, 3, 1, 10, 0, tzinfo=UTC,
                ),
                duration_minutes=45,
                created_by="emp1",
            )

    def test_create_computes_scheduled_end(self):
        start = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
        appt = Appointment.create(
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            scheduled_start=start,
            duration_minutes=60,
            created_by="emp1",
        )
        assert appt.scheduled_end == datetime(
            2026, 3, 1, 11, 0, tzinfo=UTC,
        )

    def test_create_with_location_and_reschedule(self):
        appt = Appointment.create(
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            scheduled_start=datetime(
                2026, 3, 1, 10, 0, tzinfo=UTC,
            ),
            duration_minutes=30,
            created_by="emp1",
            location="Office 3B",
            rescheduled_from_id="old_appt_1",
        )
        assert appt.location == "Office 3B"
        assert appt.rescheduled_from_id == "old_appt_1"
        assert appt.scheduled_end == datetime(
            2026, 3, 1, 10, 30, tzinfo=UTC,
        )


class TestAppointmentTransitions:

    def _make_appointment(
        self,
        status: AppointmentStatus = AppointmentStatus.PENDING,
    ) -> Appointment:
        return Appointment.create(
            company_id="comp1",
            request_id="req1",
            technician_id="tech1",
            employee_id="emp1",
            scheduled_start=datetime(
                2026, 3, 1, 10, 0, tzinfo=UTC,
            ),
            duration_minutes=60,
            created_by="emp1",
            initial_status=status,
        )

    def test_confirm_from_pending(self):
        appt = self._make_appointment()
        appt.confirm()
        assert appt.status == AppointmentStatus.CONFIRMED

    def test_confirm_from_confirmed_raises(self):
        appt = self._make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            appt.confirm()

    def test_cancel_from_pending(self):
        appt = self._make_appointment()
        appt.cancel(
            reason="Schedule conflict",
            cancelled_by="emp1",
        )
        assert appt.status == AppointmentStatus.CANCELLED
        assert appt.cancellation_reason == "Schedule conflict"
        assert appt.cancelled_by == "emp1"

    def test_cancel_from_confirmed(self):
        appt = self._make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        appt.cancel(
            reason="Emergency", cancelled_by="tech1",
        )
        assert appt.status == AppointmentStatus.CANCELLED

    def test_cancel_from_completed_raises(self):
        appt = self._make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        appt.complete()
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            appt.cancel(
                reason="Too late", cancelled_by="emp1",
            )

    def test_complete_from_confirmed(self):
        appt = self._make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        appt.complete(notes="All good")
        assert appt.status == AppointmentStatus.COMPLETED
        assert appt.completed_at is not None
        assert appt.notes == "All good"

    def test_complete_from_pending_raises(self):
        appt = self._make_appointment()
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            appt.complete()

    def test_mark_no_show(self):
        appt = self._make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        appt.mark_no_show()
        assert appt.status == AppointmentStatus.NO_SHOW

    def test_mark_no_show_from_cancelled_raises(self):
        appt = self._make_appointment()
        appt.cancel(
            reason="Changed mind", cancelled_by="emp1",
        )
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            appt.mark_no_show()

    def test_mark_reminder_24h(self):
        appt = self._make_appointment()
        assert appt.reminder_24h_sent is False
        appt.mark_reminder_sent("24h")
        assert appt.reminder_24h_sent is True

    def test_mark_reminder_1h(self):
        appt = self._make_appointment()
        assert appt.reminder_1h_sent is False
        appt.mark_reminder_sent("1h")
        assert appt.reminder_1h_sent is True

    def test_mark_reminder_invalid_type(self):
        appt = self._make_appointment()
        with pytest.raises(
            ValueError, match="Invalid reminder type",
        ):
            appt.mark_reminder_sent("2h")


class TestAppointmentStatusTerminal:

    def test_terminal_statuses(self):
        for status in [
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        ]:
            assert status.is_terminal is True

    def test_non_terminal_statuses(self):
        for status in [
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        ]:
            assert status.is_terminal is False


class TestTechnicianAvailability:

    def test_create_valid(self):
        avail = TechnicianAvailability.create(
            company_id="comp1",
            technician_id="tech1",
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert avail.day_of_week == 0
        assert avail.start_time == time(9, 0)
        assert avail.end_time == time(17, 0)

    def test_validates_day_of_week(self):
        with pytest.raises(
            ValueError, match="day_of_week must be 0-6",
        ):
            TechnicianAvailability.create(
                company_id="comp1",
                technician_id="tech1",
                day_of_week=7,
                start_time=time(9, 0),
                end_time=time(17, 0),
            )

    def test_validates_negative_day(self):
        with pytest.raises(
            ValueError, match="day_of_week must be 0-6",
        ):
            TechnicianAvailability.create(
                company_id="comp1",
                technician_id="tech1",
                day_of_week=-1,
                start_time=time(9, 0),
                end_time=time(17, 0),
            )

    def test_validates_times(self):
        with pytest.raises(
            ValueError, match="start_time must be before",
        ):
            TechnicianAvailability.create(
                company_id="comp1",
                technician_id="tech1",
                day_of_week=0,
                start_time=time(17, 0),
                end_time=time(9, 0),
            )

    def test_validates_equal_times(self):
        with pytest.raises(
            ValueError, match="start_time must be before",
        ):
            TechnicianAvailability.create(
                company_id="comp1",
                technician_id="tech1",
                day_of_week=0,
                start_time=time(9, 0),
                end_time=time(9, 0),
            )


class TestAvailabilityOverride:

    def test_create_unavailable(self):
        override = AvailabilityOverride.create(
            company_id="comp1",
            technician_id="tech1",
            target_date=date(2026, 3, 1),
            is_available=False,
            reason="Vacation",
        )
        assert override.is_available is False
        assert override.reason == "Vacation"
        assert override.start_time is None

    def test_create_available_with_times(self):
        override = AvailabilityOverride.create(
            company_id="comp1",
            technician_id="tech1",
            target_date=date(2026, 3, 7),  # Saturday
            is_available=True,
            start_time=time(10, 0),
            end_time=time(14, 0),
        )
        assert override.is_available is True
        assert override.start_time == time(10, 0)
        assert override.end_time == time(14, 0)

    def test_available_requires_times(self):
        with pytest.raises(
            ValueError,
            match="start_time and end_time are required",
        ):
            AvailabilityOverride.create(
                company_id="comp1",
                technician_id="tech1",
                target_date=date(2026, 3, 7),
                is_available=True,
            )

    def test_available_validates_time_order(self):
        with pytest.raises(
            ValueError, match="start_time must be before",
        ):
            AvailabilityOverride.create(
                company_id="comp1",
                technician_id="tech1",
                target_date=date(2026, 3, 7),
                is_available=True,
                start_time=time(14, 0),
                end_time=time(10, 0),
            )
