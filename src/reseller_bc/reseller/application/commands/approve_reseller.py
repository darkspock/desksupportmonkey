from dataclasses import dataclass

from core.config import settings
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.entities import _generate_referral_code
from src.reseller_bc.reseller.domain.exceptions import (
    ReferralCodeCollisionException,
    ResellerNotFoundException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ApproveResellerCommand(Command):
    reseller_id: str


class ApproveResellerCommandHandler(CommandHandler[ApproveResellerCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: ApproveResellerCommand) -> None:
        reseller = self.repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)

        reseller.approve()

        # Generate unique referral code if not already set or collision
        for attempt in range(3):
            if reseller.referral_code and not self.repo.exists_by_referral_code(
                reseller.referral_code
            ):
                break
            reseller.referral_code = _generate_referral_code(length=8 + attempt)
        else:
            raise ReferralCodeCollisionException()

        self.repo.save(reseller)

        # Send approval email
        from core.tasks.reseller_emails import send_reseller_approval_email

        login_url = f"{settings.FRONTEND_URL}/reseller/login"
        send_reseller_approval_email.delay(
            to_email=reseller.email,
            name=reseller.name,
            login_url=login_url,
        )
