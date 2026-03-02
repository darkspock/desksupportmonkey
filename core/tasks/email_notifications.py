import logging
import os

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings
from core.email import get_email_service

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "templates", "email"
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
_jinja_env.globals["brand_name"] = settings.BRAND_NAME
_jinja_env.globals["frontend_url"] = settings.FRONTEND_URL


@celery_app.task(
    name="core.tasks.email_notifications.send_request_notification_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_request_notification_email(
    self,
    to_email: str,
    to_name: str,
    actor_name: str,
    request_id: str,
    request_title: str,
    comment_body: str,
    variant: str,
) -> None:
    """Send email notification for request comments or waiting status."""
    try:
        template = _jinja_env.get_template(f"request_{variant}.html")
        request_url = f"{settings.FRONTEND_URL}/requests/{request_id}"

        html = template.render(
            to_name=to_name,
            actor_name=actor_name,
            request_title=request_title,
            comment_body=comment_body,
            request_url=request_url,
        )

        if variant == "action_required":
            subject = f"[{settings.BRAND_NAME}] Action required: {request_title}"
        else:
            subject = f"[{settings.BRAND_NAME}] New message on: {request_title}"

        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info(
            "Request email sent: variant=%s, to=%s, request=%s",
            variant, to_email, request_id,
        )
    except Exception as exc:
        logger.error(
            "Failed to send request email: variant=%s, to=%s, request=%s, error=%s",
            variant, to_email, request_id, str(exc),
        )
        raise self.retry(exc=exc)
