import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.config import settings
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ForgotResellerPasswordCommand(Command):
    email: str


class ForgotResellerPasswordCommandHandler(
    CommandHandler[ForgotResellerPasswordCommand]
):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: ForgotResellerPasswordCommand) -> None:
        reseller = self.repo.find_by_email(command.email)
        if reseller is None:
            # Silent return — no email enumeration
            return

        if not reseller.has_password:
            # OAuth-only account — don't send reset email
            return

        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        reseller.set_reset_token(token, expires_at)
        self.repo.save(reseller)

        from core.tasks.reseller_emails import send_reseller_password_reset_email

        reset_url = f"{settings.FRONTEND_URL}/reseller/reset-password?token={token}"
        send_reseller_password_reset_email.delay(
            to_email=reseller.email,
            name=reseller.name,
            reset_url=reset_url,
        )
