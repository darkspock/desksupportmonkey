import logging
from datetime import datetime, timedelta, timezone

from core.celery import celery_app

logger = logging.getLogger(__name__)

NO_SHOW_GRACE_HOURS = 2
REMINDER_WINDOW_MINUTES = 15


@celery_app.task(
    name="core.tasks.appointments.send_appointment_reminders",
)
def send_appointment_reminders() -> int:
    """Send 24h and 1h reminders for upcoming confirmed appointments."""
    from core.database import SessionLocal
    from src.appointment_bc.appointment.infrastructure.repository import (
        AppointmentRepository,
    )
    from src.notification_bc.notification.domain.entities import (
        Notification,
    )
    from src.notification_bc.notification.domain.enums import (
        EventType,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    total_sent = 0
    try:
        appt_repo = AppointmentRepository(session)
        notif_repo = NotificationRepository(session)
        now = datetime.now(timezone.utc)

        for reminder_type, offset_hours in [
            ("24h", 24),
            ("1h", 1),
        ]:
            window_start = now + timedelta(hours=offset_hours)
            window_end = window_start + timedelta(
                minutes=REMINDER_WINDOW_MINUTES,
            )

            appointments = appt_repo.find_needing_reminder(
                reminder_type=reminder_type,
                window_start=window_start,
                window_end=window_end,
            )

            for appt in appointments:
                start_str = appt.scheduled_start.strftime(
                    "%Y-%m-%d %H:%M",
                )
                title = f"Appointment reminder ({reminder_type})"
                body = (
                    f"Appointment on {start_str} "
                    f"for {appt.duration_minutes} min"
                )
                data = {
                    "appointment_id": appt.id,
                    "request_id": appt.request_id,
                    "reminder_type": reminder_type,
                }

                for user_id in [
                    appt.technician_id,
                    appt.employee_id,
                ]:
                    notif = Notification.create(
                        user_id=user_id,
                        company_id=appt.company_id,
                        event_type=EventType.APPOINTMENT_REMINDER.value,
                        title=title,
                        body=body,
                        data=data,
                    )
                    notif_repo.save(notif)

                appt.mark_reminder_sent(reminder_type)
                appt_repo.save(appt)
                total_sent += 1

        session.commit()
        logger.info(
            "Sent %d appointment reminders", total_sent,
        )
        return total_sent

    except Exception:
        session.rollback()
        logger.exception(
            "Appointment reminder task failed",
        )
        raise
    finally:
        session.close()


@celery_app.task(
    name="core.tasks.appointments.detect_no_shows",
)
def detect_no_shows() -> int:
    """Mark confirmed appointments as NO_SHOW if past end + grace period."""
    from core.database import SessionLocal
    from src.appointment_bc.appointment.infrastructure.repository import (
        AppointmentRepository,
    )
    from src.notification_bc.notification.domain.entities import (
        Notification,
    )
    from src.notification_bc.notification.domain.enums import (
        EventType,
    )
    from src.notification_bc.notification.infrastructure.repository import (
        NotificationRepository,
    )

    session = SessionLocal()
    count = 0
    try:
        appt_repo = AppointmentRepository(session)
        notif_repo = NotificationRepository(session)

        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=NO_SHOW_GRACE_HOURS,
        )
        overdue = appt_repo.find_confirmed_before(cutoff)

        for appt in overdue:
            appt.mark_no_show()
            appt_repo.save(appt)

            notif = Notification.create(
                user_id=appt.technician_id,
                company_id=appt.company_id,
                event_type=EventType.APPOINTMENT_REMINDER.value,
                title="Appointment no-show",
                body=(
                    f"Appointment on "
                    f"{appt.scheduled_start.strftime('%Y-%m-%d %H:%M')} "
                    f"was marked as no-show"
                ),
                data={
                    "appointment_id": appt.id,
                    "request_id": appt.request_id,
                },
            )
            notif_repo.save(notif)
            count += 1

        session.commit()
        logger.info(
            "Detected %d no-show appointments", count,
        )
        return count

    except Exception:
        session.rollback()
        logger.exception(
            "No-show detection task failed",
        )
        raise
    finally:
        session.close()
