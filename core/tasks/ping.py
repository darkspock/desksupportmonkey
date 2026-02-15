from core.celery import celery_app


@celery_app.task(name="core.tasks.ping.ping")
def ping():
    """Health check task for Celery worker."""
    return "pong"
