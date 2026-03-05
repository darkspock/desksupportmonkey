import logging
import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from core.celery import celery_app
from core.config import settings
from core.email import get_email_service

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "templates",
    "email",
)
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
_jinja_env.globals["brand_name"] = settings.BRAND_NAME
_jinja_env.globals["frontend_url"] = settings.FRONTEND_URL


@celery_app.task(
    name="core.tasks.reseller_emails.send_reseller_registration_confirmation",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_reseller_registration_confirmation(
    self,
    to_email: str,
    name: str,
) -> None:
    try:
        template = _jinja_env.get_template("reseller_registration_confirmation.html")
        html = template.render(name=name)
        subject = f"[{settings.BRAND_NAME}] We received your reseller application"
        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Reseller registration confirmation sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send reseller registration confirmation to %s: %s", to_email, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="core.tasks.reseller_emails.send_reseller_admin_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_reseller_admin_notification(
    self,
    reseller_name: str,
    reseller_email: str,
    company_name: str,
) -> None:
    try:
        template = _jinja_env.get_template("reseller_registration_admin_notification.html")
        html = template.render(
            reseller_name=reseller_name,
            reseller_email=reseller_email,
            company_name=company_name,
        )
        subject = f"[{settings.BRAND_NAME}] New reseller application from {reseller_name}"
        admin_email = settings.ADMIN_EMAIL
        email_service = get_email_service()
        email_service.send(admin_email, subject, html)
        logger.info("Reseller admin notification sent for %s", reseller_email)
    except Exception as exc:
        logger.error("Failed to send reseller admin notification for %s: %s", reseller_email, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="core.tasks.reseller_emails.send_reseller_approval_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_reseller_approval_email(
    self,
    to_email: str,
    name: str,
    login_url: str,
) -> None:
    try:
        template = _jinja_env.get_template("reseller_approved.html")
        html = template.render(name=name, login_url=login_url)
        subject = f"[{settings.BRAND_NAME}] Your reseller application has been approved!"
        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Reseller approval email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send reseller approval email to %s: %s", to_email, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="core.tasks.reseller_emails.send_reseller_rejection_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_reseller_rejection_email(
    self,
    to_email: str,
    name: str,
    reason: Optional[str] = None,
) -> None:
    try:
        template = _jinja_env.get_template("reseller_rejected.html")
        html = template.render(name=name, reason=reason)
        subject = f"[{settings.BRAND_NAME}] Update on your reseller application"
        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Reseller rejection email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send reseller rejection email to %s: %s", to_email, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="core.tasks.reseller_emails.send_reseller_password_reset_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_reseller_password_reset_email(
    self,
    to_email: str,
    name: str,
    reset_url: str,
) -> None:
    try:
        template = _jinja_env.get_template("reseller_password_reset.html")
        html = template.render(name=name, reset_url=reset_url)
        subject = f"[{settings.BRAND_NAME}] Reset your password"
        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Reseller password reset email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send reseller password reset email to %s: %s", to_email, str(exc))
        raise self.retry(exc=exc)
