from datetime import datetime, timedelta, timezone, UTC
from unittest.mock import MagicMock, patch

from src.appointment_bc.appointment.domain.entities import Appointment
from src.appointment_bc.appointment.domain.enums import AppointmentStatus


def _make_appointment(
    status: AppointmentStatus = AppointmentStatus.CONFIRMED,
    start_offset_hours: int = 24,
) -> Appointment:
    now = datetime.now(UTC)
    start = now + timedelta(hours=start_offset_hours)
    return Appointment.create(
        company_id="comp1",
        request_id="req1",
        technician_id="tech1",
        employee_id="emp1",
        scheduled_start=start,
        duration_minutes=60,
        created_by="tech1",
        initial_status=status,
    )


class TestSendAppointmentReminders:

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.appointment_bc.appointment.infrastructure.repository.AppointmentRepository")
    @patch("core.database.SessionLocal")
    def test_send_24h_reminders(
        self, MockSession, MockApptRepo, MockNotifRepo,
    ):
        from core.tasks.appointments import (
            send_appointment_reminders,
        )

        session = MagicMock()
        MockSession.return_value = session

        appt = _make_appointment(start_offset_hours=24)
        appt_repo = MagicMock()
        appt_repo.find_needing_reminder.side_effect = [
            [appt],  # 24h window
            [],  # 1h window
        ]
        MockApptRepo.return_value = appt_repo

        notif_repo = MagicMock()
        MockNotifRepo.return_value = notif_repo

        result = send_appointment_reminders()

        assert result == 1
        assert appt_repo.save.call_count == 1
        # 2 notifications: technician + employee
        assert notif_repo.save.call_count == 2
        assert appt.reminder_24h_sent is True
        session.commit.assert_called_once()

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.appointment_bc.appointment.infrastructure.repository.AppointmentRepository")
    @patch("core.database.SessionLocal")
    def test_send_1h_reminders(
        self, MockSession, MockApptRepo, MockNotifRepo,
    ):
        from core.tasks.appointments import (
            send_appointment_reminders,
        )

        session = MagicMock()
        MockSession.return_value = session

        appt = _make_appointment(start_offset_hours=1)
        appt_repo = MagicMock()
        appt_repo.find_needing_reminder.side_effect = [
            [],  # 24h window
            [appt],  # 1h window
        ]
        MockApptRepo.return_value = appt_repo

        notif_repo = MagicMock()
        MockNotifRepo.return_value = notif_repo

        result = send_appointment_reminders()

        assert result == 1
        assert appt.reminder_1h_sent is True
        session.commit.assert_called_once()

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.appointment_bc.appointment.infrastructure.repository.AppointmentRepository")
    @patch("core.database.SessionLocal")
    def test_no_reminders_when_none_found(
        self, MockSession, MockApptRepo, MockNotifRepo,
    ):
        from core.tasks.appointments import (
            send_appointment_reminders,
        )

        session = MagicMock()
        MockSession.return_value = session

        appt_repo = MagicMock()
        appt_repo.find_needing_reminder.return_value = []
        MockApptRepo.return_value = appt_repo

        result = send_appointment_reminders()

        assert result == 0
        appt_repo.save.assert_not_called()
        session.commit.assert_called_once()


class TestDetectNoShows:

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.appointment_bc.appointment.infrastructure.repository.AppointmentRepository")
    @patch("core.database.SessionLocal")
    def test_detect_no_shows(
        self, MockSession, MockApptRepo, MockNotifRepo,
    ):
        from core.tasks.appointments import detect_no_shows

        session = MagicMock()
        MockSession.return_value = session

        appt = _make_appointment(start_offset_hours=-4)
        appt_repo = MagicMock()
        appt_repo.find_confirmed_before.return_value = [appt]
        MockApptRepo.return_value = appt_repo

        notif_repo = MagicMock()
        MockNotifRepo.return_value = notif_repo

        result = detect_no_shows()

        assert result == 1
        assert appt.status == AppointmentStatus.NO_SHOW
        appt_repo.save.assert_called_once()
        notif_repo.save.assert_called_once()
        session.commit.assert_called_once()

    @patch("src.notification_bc.notification.infrastructure.repository.NotificationRepository")
    @patch("src.appointment_bc.appointment.infrastructure.repository.AppointmentRepository")
    @patch("core.database.SessionLocal")
    def test_detect_no_shows_none_found(
        self, MockSession, MockApptRepo, MockNotifRepo,
    ):
        from core.tasks.appointments import detect_no_shows

        session = MagicMock()
        MockSession.return_value = session

        appt_repo = MagicMock()
        appt_repo.find_confirmed_before.return_value = []
        MockApptRepo.return_value = appt_repo

        result = detect_no_shows()

        assert result == 0
        appt_repo.save.assert_not_called()
        session.commit.assert_called_once()
