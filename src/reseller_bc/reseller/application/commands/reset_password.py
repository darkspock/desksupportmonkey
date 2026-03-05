from dataclasses import dataclass
from datetime import datetime, timezone

from core.password import PasswordService
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerInvalidPasswordException,
    ResellerInvalidResetTokenException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ResetResellerPasswordCommand(Command):
    token: str
    new_password: str


class ResetResellerPasswordCommandHandler(
    CommandHandler[ResetResellerPasswordCommand]
):
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        password_service: PasswordService,
    ):
        self.repo = repo
        self.password_service = password_service

    def handle(self, command: ResetResellerPasswordCommand) -> None:
        reseller = self.repo.find_by_reset_token(command.token)
        if reseller is None:
            raise ResellerInvalidResetTokenException()

        if (
            reseller.reset_token_expires_at is None
            or reseller.reset_token_expires_at < datetime.now(timezone.utc)
        ):
            raise ResellerInvalidResetTokenException("Reset token has expired")

        if len(command.new_password) < 8:
            raise ResellerInvalidPasswordException(
                "Password must be at least 8 characters"
            )

        reseller.set_password_hash(
            self.password_service.hash_password(command.new_password)
        )
        reseller.clear_reset_token()
        self.repo.save(reseller)
