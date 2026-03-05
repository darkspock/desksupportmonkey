import logging

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings
from core.email import get_email_service

logger = logging.getLogger(__name__)

_env = Environment(loader=FileSystemLoader("templates/email"))
_env.globals["brand_name"] = settings.BRAND_NAME
_env.globals["frontend_url"] = settings.FRONTEND_URL


@celery_app.task(
    name="core.tasks.support_ticket_emails.send_support_ticket_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_support_ticket_email(
    self,
    to_email: str,
    to_name: str,
    ticket_reference: str,
    ticket_subject: str,
    variant: str,
    message_body: str = "",
    responder_name: str = "",
):
    """Send support ticket email with one of 3 variants.

    Args:
        variant: "ticket_created" | "response_received" | "ticket_resolved"
    """
    try:
        template = _env.get_template(f"support_{variant}.html")
        html = template.render(
            to_name=to_name,
            ticket_reference=ticket_reference,
            ticket_subject=ticket_subject,
            message_body=message_body,
            responder_name=responder_name,
            ticket_url=f"{settings.FRONTEND_URL}/support/tickets",
        )

        subject_map = {
            "ticket_created": f"[{settings.BRAND_NAME}] Ticket {ticket_reference}: {ticket_subject}",
            "response_received": f"[{settings.BRAND_NAME}] New response on {ticket_reference}: {ticket_subject}",
            "ticket_resolved": f"[{settings.BRAND_NAME}] Ticket resolved: {ticket_reference}",
        }
        subject = subject_map.get(variant, f"[{settings.BRAND_NAME}] Support ticket update")

        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Sent %s email for %s to %s", variant, ticket_reference, to_email)
    except Exception as exc:
        logger.exception("Failed to send %s email for %s", variant, ticket_reference)
        raise self.retry(exc=exc)
