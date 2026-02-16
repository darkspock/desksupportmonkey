import logging
from abc import ABC, abstractmethod

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class EmailServiceInterface(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> None:
        ...


class BrevoEmailService(EmailServiceInterface):
    """Send transactional emails via Brevo HTTP API."""

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def send(self, to: str, subject: str, html_body: str) -> None:
        payload = {
            "sender": {
                "name": settings.SMTP_FROM_NAME,
                "email": settings.SMTP_FROM_EMAIL,
            },
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html_body,
        }
        try:
            resp = httpx.post(
                self.API_URL,
                json=payload,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if resp.status_code >= 400:
                detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                logger.error("Brevo API error sending to %s: %s %s", to, resp.status_code, detail)
                raise RuntimeError(f"Brevo API {resp.status_code}: {detail}")
            logger.info("Email sent to %s via Brevo: %s (messageId=%s)", to, subject, resp.json().get("messageId"))
        except httpx.HTTPError as e:
            logger.error("Brevo HTTP error sending to %s: %s", to, str(e))
            raise


class ConsoleEmailService(EmailServiceInterface):
    """Development email service that logs to console."""

    def send(self, to: str, subject: str, html_body: str) -> None:
        logger.info("=== EMAIL (dev mode) ===")
        logger.info("To: %s", to)
        logger.info("Subject: %s", subject)
        logger.info("Body: %s", html_body)


def get_email_service() -> EmailServiceInterface:
    """Brevo in production (BREVO_API_KEY set), console in dev."""
    if settings.BREVO_API_KEY:
        return BrevoEmailService()
    return ConsoleEmailService()


def send_magic_link_email(email_service: EmailServiceInterface, to: str, token: str) -> None:
    """Send magic link email with the verification link."""
    link = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
    html = f"""
    <html>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2>Sign in to DeskSupportMonkey</h2>
        <p>Click the link below to sign in:</p>
        <p><a href="{link}" style="display: inline-block; padding: 12px 24px;
            background-color: #2563eb; color: white; text-decoration: none;
            border-radius: 6px;">Sign In</a></p>
        <p style="color: #666; font-size: 14px;">
            This link expires in 24 hours and can only be used once.
        </p>
        <p style="color: #999; font-size: 12px;">
            If you didn't request this, you can safely ignore this email.
        </p>
    </body>
    </html>
    """
    email_service.send(to, "Sign in to DeskSupportMonkey", html)


def send_admin_promotion_email(
    email_service: EmailServiceInterface,
    to: str,
    new_admin_email: str,
    company_name: str,
) -> None:
    """Notify existing admins when a new admin is promoted."""
    html = f"""
    <html>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2>New Admin Promoted</h2>
        <p><strong>{new_admin_email}</strong> has been promoted to admin
        in your organization.</p>
        <p style="color: #666; font-size: 14px;">
            If you did not expect this change, please review your team's admin settings.
        </p>
    </body>
    </html>
    """
    email_service.send(to, "New admin promoted - DeskSupportMonkey", html)
