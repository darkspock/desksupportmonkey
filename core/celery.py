from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery(
    "desksupportmonkey",
    broker=settings.celery.CELERY_BROKER_URL,
    backend=settings.celery.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Task settings
    task_time_limit=settings.celery.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.celery.CELERY_TASK_SOFT_TIME_LIMIT,

    # Result settings
    result_expires=3600,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Serialization settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routes
    task_routes={
        "core.tasks.*": {"queue": "reports"},
    },

    # Beat schedule
    beat_schedule={
        "cleanup-magic-links": {
            "task": "core.tasks.cleanup.cleanup_magic_links",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
            "kwargs": {"days": 7},
        },
        "send-appointment-reminders": {
            "task": "core.tasks.appointments.send_appointment_reminders",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "detect-appointment-no-shows": {
            "task": "core.tasks.appointments.detect_no_shows",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "send-maintenance-reminders": {
            "task": "core.tasks.maintenance.send_maintenance_reminders",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "check-overdue-maintenance": {
            "task": "core.tasks.maintenance.check_overdue_maintenance",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "generate-recurring-maintenance": {
            "task": "core.tasks.maintenance.generate_recurring_maintenance",
            "schedule": crontab(minute=0, hour=2),  # Daily 02:00 UTC
        },
        "check-regulatory-deadlines": {
            "task": "core.tasks.incidents.check_regulatory_deadlines",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "check-risk-overdue-reviews": {
            "task": "core.tasks.risks.check_overdue_reviews",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        },
        "check-sla-breaches": {
            "task": "core.tasks.sla.check_sla_breaches",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "audit-retention-purge": {
            "task": "core.tasks.audit.retention_purge",
            "schedule": crontab(
                hour=3, minute=0, day_of_week="sunday"
            ),  # Weekly Sunday 03:00 UTC
        },
        "expire-vendor-contracts": {
            "task": "core.tasks.vendor_contracts.expire_active_contracts",
            "schedule": crontab(hour=1, minute=0),  # Daily at 01:00 UTC
        },
        "check-contract-renewals": {
            "task": "core.tasks.vendor_contracts.send_contract_renewal_reminders",
            "schedule": crontab(hour=6, minute=0),  # Daily at 06:00 UTC
        },
        "check-concentration-risk": {
            "task": "core.tasks.vendor_contracts.check_concentration_risk",
            "schedule": crontab(hour=7, minute=0),  # Daily at 07:00 UTC
        },
        "check-stale-assessments": {
            "task": "core.tasks.vendor_contracts.check_stale_assessments",
            "schedule": crontab(hour=7, minute=30),  # Daily at 07:30 UTC
        },
    },
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["core.tasks"])
