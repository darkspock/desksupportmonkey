from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import ResellerAlreadyExistsException
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class RegisterResellerOAuthCommand(Command):
    name: str
    email: str
    company_name: str
    provider_field: str  # "google_id" or "microsoft_id"
    provider_id: str


class RegisterResellerOAuthCommandHandler(CommandHandler[RegisterResellerOAuthCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: RegisterResellerOAuthCommand) -> None:
        if self.repo.exists_by_email(command.email):
            raise ResellerAlreadyExistsException(command.email)

        reseller = Reseller.create(
            email=command.email,
            name=command.name,
            commission_pct=20,
            min_payout_cents=5000,
            status=ResellerStatus.PENDING,
            company_name=command.company_name,
        )

        if command.provider_field == "google_id":
            reseller.link_google(command.provider_id)
        elif command.provider_field == "microsoft_id":
            reseller.link_microsoft(command.provider_id)

        self.repo.save(reseller)

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
