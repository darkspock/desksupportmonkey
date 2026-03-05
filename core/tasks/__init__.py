from core.tasks.ping import ping
from core.tasks.cleanup import cleanup_magic_links
from core.tasks.appointments import send_appointment_reminders, detect_no_shows
from core.tasks.maintenance import (
    send_maintenance_reminders,
    check_overdue_maintenance,
    generate_recurring_maintenance,
)
from core.tasks.reports import generate_report, generate_po_pdf
from core.tasks.incidents import generate_incident_report, check_regulatory_deadlines
from core.tasks.risks import check_overdue_reviews
from core.tasks.sla import check_sla_breaches
from core.tasks.audit import export_audit_log, verify_audit_integrity, retention_purge
from core.tasks.gdpr import gdpr_data_export, gdpr_anonymize_user
from core.tasks.compliance import generate_compliance_report

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
    "generate_incident_report",
    "check_regulatory_deadlines",
    "check_overdue_reviews",
    "check_sla_breaches",
    "export_audit_log",
    "verify_audit_integrity",
    "retention_purge",
    "gdpr_data_export",
    "gdpr_anonymize_user",
    "generate_compliance_report",
]
