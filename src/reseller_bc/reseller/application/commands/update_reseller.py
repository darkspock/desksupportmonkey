from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import ResellerNotFoundException
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class UpdateResellerCommand(Command):
    reseller_id: str
    commission_pct: Optional[int] = None
    min_payout_cents: Optional[int] = None
    status: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    referral_code: Optional[str] = None


class UpdateResellerCommandHandler(CommandHandler[UpdateResellerCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateResellerCommand) -> None:
        reseller = self.repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)

        status = ResellerStatus(command.status) if command.status else None
        reseller.update_settings(
            commission_pct=command.commission_pct,
            min_payout_cents=command.min_payout_cents,
            status=status,
            name=command.name,
            email=command.email,
            company_name=command.company_name,
            tax_id=command.tax_id,
            referral_code=command.referral_code,
        )
        self.repo.save(reseller)
