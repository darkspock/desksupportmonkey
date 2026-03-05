from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.entities import Reseller, _generate_referral_code
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerAlreadyExistsException,
    ReferralCodeCollisionException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class CreateResellerCommand(Command):
    id: str
    email: str
    name: str
    commission_pct: int
    min_payout_cents: int


class CreateResellerCommandHandler(CommandHandler[CreateResellerCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: CreateResellerCommand) -> None:
        if self.repo.exists_by_email(command.email):
            raise ResellerAlreadyExistsException(command.email)

        reseller = Reseller.create(
            id=command.id,
            email=command.email,
            name=command.name,
            commission_pct=command.commission_pct,
            min_payout_cents=command.min_payout_cents,
        )

        # Retry referral code generation on collision (max 3 attempts)
        for attempt in range(3):
            if not self.repo.exists_by_referral_code(reseller.referral_code):
                break
            reseller.referral_code = _generate_referral_code(length=8 + attempt)
        else:
            raise ReferralCodeCollisionException()

        self.repo.save(reseller)
