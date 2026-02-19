from core.tasks.ping import ping
from core.tasks.cleanup import cleanup_magic_links
from core.tasks.appointments import send_appointment_reminders, detect_no_shows
from core.tasks.maintenance import (
    send_maintenance_reminders,
    check_overdue_maintenance,
    generate_recurring_maintenance,
)
from core.tasks.reports import generate_report, generate_po_pdf

__all__ = [
    "ping",
    "cleanup_magic_links",
    "send_appointment_reminders",
    "detect_no_shows",
    "send_maintenance_reminders",
    "check_overdue_maintenance",
    "generate_recurring_maintenance",
    "generate_report",
    "generate_po_pdf",
]
