import logging
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings

logger = logging.getLogger(__name__)


class EmailServiceInterface(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> None:
        ...


class SMTPEmailService(EmailServiceInterface):
    def send(self, to: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, str(e))
            raise


class ConsoleEmailService(EmailServiceInterface):
    """Development email service that prints to console."""

    def send(self, to: str, subject: str, html_body: str) -> None:
        logger.info("=== EMAIL (dev mode) ===")
        logger.info("To: %s", to)
        logger.info("Subject: %s", subject)
        logger.info("Body: %s", html_body)


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
