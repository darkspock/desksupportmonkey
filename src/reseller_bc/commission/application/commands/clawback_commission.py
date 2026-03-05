from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.enums import CommissionStatus
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface


@dataclass
class ClawbackCommissionCommand(Command):
    stripe_invoice_id: str


class ClawbackCommissionCommandHandler(CommandHandler[ClawbackCommissionCommand]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        self.commission_repo = commission_repo

    def handle(self, command: ClawbackCommissionCommand) -> None:
        # 1. Find commission by stripe_invoice_id
        commission = self.commission_repo.find_by_stripe_invoice_id(command.stripe_invoice_id)
        if commission is None:
            return  # No commission for this invoice — skip

        # 2. If already clawed back, skip
        if commission.status == CommissionStatus.CLAWED_BACK:
            return

        # 3. If already paid, create negative record
        if commission.status == CommissionStatus.PAID:
            negative = ResellerCommission.create_clawback(commission)
            self.commission_repo.save(negative)

        # 4. Mark original as clawed_back
        commission.clawback()
        self.commission_repo.save(commission)
