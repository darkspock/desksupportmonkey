from datetime import datetime, UTC
from unittest.mock import MagicMock

import pytest

from src.appointment_bc.appointment.application.commands.cancel_appointment import (
    CancelAppointmentCommand,
    CancelAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.complete_appointment import (
    CompleteAppointmentCommand,
    CompleteAppointmentCommandHandler,
)
from src.appointment_bc.appointment.application.commands.confirm_appointment import (
    AppointmentNotFoundError,
    ConfirmAppointmentCommand,
    ConfirmAppointmentCommandHandler,
)
from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
    InvalidAppointmentStatusTransitionError,
)


def _make_appointment(
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
        created_by="tech1",
        initial_status=status,
    )


class TestConfirmAppointment:

    def test_confirm_appointment(self):
        appt = _make_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = ConfirmAppointmentCommandHandler(
            appointment_repo=repo,
        )
        handler.handle(
            ConfirmAppointmentCommand(
                appointment_id=appt.id,
                company_id="comp1",
                performed_by="tech1",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.status == AppointmentStatus.CONFIRMED

    def test_confirm_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = ConfirmAppointmentCommandHandler(
            appointment_repo=repo,
        )
        with pytest.raises(AppointmentNotFoundError):
            handler.handle(
                ConfirmAppointmentCommand(
                    appointment_id="bad_id",
                    company_id="comp1",
                    performed_by="tech1",
                )
            )


class TestCancelAppointment:

    def test_cancel_with_reason(self):
        appt = _make_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = CancelAppointmentCommandHandler(
            appointment_repo=repo,
        )
        handler.handle(
            CancelAppointmentCommand(
                appointment_id=appt.id,
                company_id="comp1",
                reason="Schedule conflict",
                performed_by="emp1",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.status == AppointmentStatus.CANCELLED
        assert saved.cancellation_reason == "Schedule conflict"
        assert saved.cancelled_by == "emp1"

    def test_cancel_completed_raises(self):
        appt = _make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        appt.complete()
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = CancelAppointmentCommandHandler(
            appointment_repo=repo,
        )
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            handler.handle(
                CancelAppointmentCommand(
                    appointment_id=appt.id,
                    company_id="comp1",
                    reason="Too late",
                    performed_by="emp1",
                )
            )


class TestCompleteAppointment:

    def test_complete_appointment(self):
        appt = _make_appointment(
            AppointmentStatus.CONFIRMED,
        )
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = CompleteAppointmentCommandHandler(
            appointment_repo=repo,
        )
        handler.handle(
            CompleteAppointmentCommand(
                appointment_id=appt.id,
                company_id="comp1",
                performed_by="tech1",
                notes="All done",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.status == AppointmentStatus.COMPLETED
        assert saved.completed_at is not None
        assert saved.notes == "All done"

    def test_complete_pending_raises(self):
        appt = _make_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = CompleteAppointmentCommandHandler(
            appointment_repo=repo,
        )
        with pytest.raises(
            InvalidAppointmentStatusTransitionError,
        ):
            handler.handle(
                CompleteAppointmentCommand(
                    appointment_id=appt.id,
                    company_id="comp1",
                    performed_by="tech1",
                )
            )
