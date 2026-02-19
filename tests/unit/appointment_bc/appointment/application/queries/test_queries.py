from datetime import datetime, UTC
from unittest.mock import MagicMock

import pytest

from src.appointment_bc.appointment.application.queries.get_appointment import (
    AppointmentNotFoundError,
    GetAppointmentQuery,
    GetAppointmentQueryHandler,
)
from src.appointment_bc.appointment.application.queries.list_appointments import (
    ListAppointmentsQuery,
    ListAppointmentsQueryHandler,
)
from src.appointment_bc.appointment.domain.entities import (
    Appointment,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)


def _make_appointment() -> Appointment:
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


class TestListAppointments:

    def test_list_returns_paginated(self):
        appt = _make_appointment()
        repo = MagicMock()
        repo.find_all.return_value = ([appt], 1)
        handler = ListAppointmentsQueryHandler(
            appointment_repo=repo,
        )
        appointments, total = handler.handle(
            ListAppointmentsQuery(
                company_id="comp1",
                page=1,
                page_size=20,
            )
        )
        assert len(appointments) == 1
        assert total == 1
        repo.find_all.assert_called_once()


class TestGetAppointment:

    def test_get_returns_appointment(self):
        appt = _make_appointment()
        repo = MagicMock()
        repo.find_by_id.return_value = appt
        handler = GetAppointmentQueryHandler(
            appointment_repo=repo,
        )
        result = handler.handle(
            GetAppointmentQuery(
                appointment_id=appt.id,
                company_id="comp1",
            )
        )
        assert result.id == appt.id

    def test_get_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetAppointmentQueryHandler(
            appointment_repo=repo,
        )
        with pytest.raises(AppointmentNotFoundError):
            handler.handle(
                GetAppointmentQuery(
                    appointment_id="bad_id",
                    company_id="comp1",
                )
            )
