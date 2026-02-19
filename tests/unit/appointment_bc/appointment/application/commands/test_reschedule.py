from datetime import datetime, UTC
from unittest.mock import MagicMock

import pytest
import ulid

from src.appointment_bc.appointment.application.commands.create_appointment import (
    AppointmentOverlapError,
)
from src.appointment_bc.appointment.application.commands.reschedule_appointment import (
    AppointmentNotFoundError,
    RescheduleAppointmentCommand,
    RescheduleAppointmentCommandHandler,
)
from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)


def _make_confirmed_appointment() -> Appointment:
    return Appointment.create(
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


class TestRescheduleAppointment:

    def test_reschedule_cancels_old_creates_new(self):
        old = _make_confirmed_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = old
        repo.find_by_technician_date_range.return_value = []
        repo.find_by_employee_date_range.return_value = []

        handler = RescheduleAppointmentCommandHandler(
            appointment_repo=repo,
        )
        new_id = ulid.new().str
        handler.handle(
            RescheduleAppointmentCommand(
                new_appointment_id=new_id,
                appointment_id=old.id,
                company_id="comp1",
                new_start=datetime(
                    2026, 3, 2, 14, 0, tzinfo=UTC,
                ),
                new_duration_minutes=60,
                performed_by="tech1",
                creator_role="technician",
                reason="Client request",
            )
        )

        assert new_id is not None
        # save called twice: old cancelled + new created
        assert repo.save.call_count == 2
        old_saved = repo.save.call_args_list[0][0][0]
        new_saved = repo.save.call_args_list[1][0][0]
        assert old_saved.status == AppointmentStatus.CANCELLED
        assert "Rescheduled" in old_saved.cancellation_reason

    def test_reschedule_links_rescheduled_from_id(self):
        old = _make_confirmed_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = old
        repo.find_by_technician_date_range.return_value = []
        repo.find_by_employee_date_range.return_value = []

        handler = RescheduleAppointmentCommandHandler(
            appointment_repo=repo,
        )
        handler.handle(
            RescheduleAppointmentCommand(
                new_appointment_id=ulid.new().str,
                appointment_id=old.id,
                company_id="comp1",
                new_start=datetime(
                    2026, 3, 2, 14, 0, tzinfo=UTC,
                ),
                new_duration_minutes=60,
                performed_by="tech1",
                creator_role="technician",
                reason="Reschedule",
            )
        )
        new_saved = repo.save.call_args_list[1][0][0]
        assert new_saved.rescheduled_from_id == old.id

    def test_reschedule_overlap_raises(self):
        old = _make_confirmed_appointment()
        overlap = MagicMock()
        repo = MagicMock()
        repo.find_by_id.return_value = old
        repo.find_by_technician_date_range.return_value = [
            overlap,
        ]
        repo.find_by_employee_date_range.return_value = []

        handler = RescheduleAppointmentCommandHandler(
            appointment_repo=repo,
        )
        with pytest.raises(AppointmentOverlapError):
            handler.handle(
                RescheduleAppointmentCommand(
                    new_appointment_id=ulid.new().str,
                    appointment_id=old.id,
                    company_id="comp1",
                    new_start=datetime(
                        2026, 3, 2, 14, 0, tzinfo=UTC,
                    ),
                    new_duration_minutes=60,
                    performed_by="tech1",
                    creator_role="technician",
                    reason="Move",
                )
            )

    def test_reschedule_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = RescheduleAppointmentCommandHandler(
            appointment_repo=repo,
        )
        with pytest.raises(AppointmentNotFoundError):
            handler.handle(
                RescheduleAppointmentCommand(
                    new_appointment_id=ulid.new().str,
                    appointment_id="bad_id",
                    company_id="comp1",
                    new_start=datetime(
                        2026, 3, 2, 14, 0, tzinfo=UTC,
                    ),
                    new_duration_minutes=60,
                    performed_by="tech1",
                    creator_role="technician",
                    reason="Move",
                )
            )
