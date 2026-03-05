from dataclasses import dataclass

from core.password import PasswordService
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerInvalidPasswordException,
    ResellerNotFoundException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ChangeResellerPasswordCommand(Command):
    reseller_id: str
    current_password: str
    new_password: str


class ChangeResellerPasswordCommandHandler(
    CommandHandler[ChangeResellerPasswordCommand]
):
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        password_service: PasswordService,
    ):
        self.repo = repo
        self.password_service = password_service

    def handle(self, command: ChangeResellerPasswordCommand) -> None:
        reseller = self.repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)

        if not reseller.has_password:
            raise ResellerInvalidPasswordException(
                "Cannot change password for OAuth-only account"
            )

        assert reseller.password_hash is not None  # guaranteed by has_password
        if not self.password_service.verify_password(
            command.current_password, reseller.password_hash
        ):
            raise ResellerInvalidPasswordException("Current password is incorrect")

        if len(command.new_password) < 8:
            raise ResellerInvalidPasswordException(
                "New password must be at least 8 characters"
            )

        reseller.set_password_hash(
            self.password_service.hash_password(command.new_password)
        )
        self.repo.save(reseller)
