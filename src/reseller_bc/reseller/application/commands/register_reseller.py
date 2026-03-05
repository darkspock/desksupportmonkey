from dataclasses import dataclass

from core.password import PasswordService
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerAlreadyExistsException,
    ResellerInvalidPasswordException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class RegisterResellerCommand(Command):
    name: str
    email: str
    company_name: str
    password: str


class RegisterResellerCommandHandler(CommandHandler[RegisterResellerCommand]):
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        password_service: PasswordService,
    ):
        self.repo = repo
        self.password_service = password_service

    def handle(self, command: RegisterResellerCommand) -> None:
        if self.repo.exists_by_email(command.email):
            raise ResellerAlreadyExistsException(command.email)

        if len(command.password) < 8:
            raise ResellerInvalidPasswordException(
                "Password must be at least 8 characters"
            )

        password_hash = self.password_service.hash_password(command.password)

        reseller = Reseller.create(
            email=command.email,
            name=command.name,
            commission_pct=20,
            min_payout_cents=5000,
            status=ResellerStatus.PENDING,
            password_hash=password_hash,
            company_name=command.company_name,
        )

        self.repo.save(reseller)

        # Send emails via Celery tasks
        from core.tasks.reseller_emails import (
            send_reseller_registration_confirmation,
            send_reseller_admin_notification,
        )

        send_reseller_registration_confirmation.delay(
            to_email=reseller.email,
            name=reseller.name,
        )
        send_reseller_admin_notification.delay(
            reseller_name=reseller.name,
            reseller_email=reseller.email,
            company_name=command.company_name,
        )
