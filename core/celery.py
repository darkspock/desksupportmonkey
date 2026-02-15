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
    },
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["core.tasks"])
