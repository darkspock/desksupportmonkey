from datetime import datetime, UTC
from unittest.mock import MagicMock

import pytest
import ulid

from src.appointment_bc.appointment.application.commands.create_appointment import (
    AppointmentOverlapError,
    CreateAppointmentCommand,
    CreateAppointmentCommandHandler,
)
from src.appointment_bc.appointment.domain.enums import (
    AppointmentStatus,
)


class TestCreateAppointmentCommand:

    def _make_handler(
        self,
        tech_overlaps=None,
        emp_overlaps=None,
    ):
        repo = MagicMock()
        repo.find_by_technician_date_range.return_value = (
            tech_overlaps or []
        )
        repo.find_by_employee_date_range.return_value = (
            emp_overlaps or []
        )
        return CreateAppointmentCommandHandler(
            appointment_repo=repo,
        ), repo

    def test_create_as_technician_confirmed(self):
        handler, repo = self._make_handler()
        appt_id = ulid.new().str
        handler.handle(
            CreateAppointmentCommand(
                appointment_id=appt_id,
                company_id="comp1",
                request_id="req1",
                technician_id="tech1",
                employee_id="emp1",
                scheduled_start=datetime(
                    2026, 3, 1, 10, 0, tzinfo=UTC,
                ),
                duration_minutes=60,
                created_by="tech1",
                creator_role="technician",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.id == appt_id
        assert saved.status == AppointmentStatus.CONFIRMED

    def test_create_as_employee_pending(self):
        handler, repo = self._make_handler()
        handler.handle(
            CreateAppointmentCommand(
                appointment_id=ulid.new().str,
                company_id="comp1",
                request_id="req1",
                technician_id="tech1",
                employee_id="emp1",
                scheduled_start=datetime(
                    2026, 3, 1, 10, 0, tzinfo=UTC,
                ),
                duration_minutes=60,
                created_by="emp1",
                creator_role="employee",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.status == AppointmentStatus.PENDING

    def test_create_as_admin_confirmed(self):
        handler, repo = self._make_handler()
        handler.handle(
            CreateAppointmentCommand(
                appointment_id=ulid.new().str,
                company_id="comp1",
                request_id="req1",
                technician_id="tech1",
                employee_id="emp1",
                scheduled_start=datetime(
                    2026, 3, 1, 10, 0, tzinfo=UTC,
                ),
                duration_minutes=60,
                created_by="admin1",
                creator_role="admin",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.status == AppointmentStatus.CONFIRMED

    def test_create_invalid_duration_raises(self):
        handler, _ = self._make_handler()
        with pytest.raises(ValueError, match="30, 60, 90"):
            handler.handle(
                CreateAppointmentCommand(
                    appointment_id=ulid.new().str,
                    company_id="comp1",
                    request_id="req1",
                    technician_id="tech1",
                    employee_id="emp1",
                    scheduled_start=datetime(
                        2026, 3, 1, 10, 0, tzinfo=UTC,
                    ),
                    duration_minutes=45,
                    created_by="tech1",
                    creator_role="technician",
                )
            )

    def test_create_technician_overlap_raises(self):
        overlap = MagicMock()
        handler, _ = self._make_handler(
            tech_overlaps=[overlap],
        )
        with pytest.raises(
            AppointmentOverlapError, match="Technician",
        ):
            handler.handle(
                CreateAppointmentCommand(
                    appointment_id=ulid.new().str,
                    company_id="comp1",
                    request_id="req1",
                    technician_id="tech1",
                    employee_id="emp1",
                    scheduled_start=datetime(
                        2026, 3, 1, 10, 0, tzinfo=UTC,
                    ),
                    duration_minutes=60,
                    created_by="tech1",
                    creator_role="technician",
                )
            )

    def test_create_employee_overlap_raises(self):
        overlap = MagicMock()
        handler, _ = self._make_handler(
            emp_overlaps=[overlap],
        )
        with pytest.raises(
            AppointmentOverlapError, match="Employee",
        ):
            handler.handle(
                CreateAppointmentCommand(
                    appointment_id=ulid.new().str,
                    company_id="comp1",
                    request_id="req1",
                    technician_id="tech1",
                    employee_id="emp1",
                    scheduled_start=datetime(
                        2026, 3, 1, 10, 0, tzinfo=UTC,
                    ),
                    duration_minutes=60,
                    created_by="tech1",
                    creator_role="technician",
                )
            )

    def test_create_with_rescheduled_from_id(self):
        handler, repo = self._make_handler()
        handler.handle(
            CreateAppointmentCommand(
                appointment_id=ulid.new().str,
                company_id="comp1",
                request_id="req1",
                technician_id="tech1",
                employee_id="emp1",
                scheduled_start=datetime(
                    2026, 3, 1, 10, 0, tzinfo=UTC,
                ),
                duration_minutes=60,
                created_by="tech1",
                creator_role="technician",
                rescheduled_from_id="old_appt_1",
            )
        )
        saved = repo.save.call_args[0][0]
        assert saved.rescheduled_from_id == "old_appt_1"
