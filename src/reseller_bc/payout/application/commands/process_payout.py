from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.payout.domain.exceptions import PayoutNotFoundException
from src.reseller_bc.payout.domain.repository import ResellerPayoutRepositoryInterface


@dataclass
class ProcessPayoutCommand(Command):
    payout_id: str
    action: str
    processed_by: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class ProcessPayoutCommandHandler(CommandHandler[ProcessPayoutCommand]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        commission_repo: ResellerCommissionRepositoryInterface,
    ):
        self.payout_repo = payout_repo
        self.commission_repo = commission_repo

    def handle(self, command: ProcessPayoutCommand) -> None:
        payout = self.payout_repo.find_by_id(command.payout_id)
        if payout is None:
            raise PayoutNotFoundException(command.payout_id)

        if command.action == "approve":
            payout.approve(processed_by=command.processed_by)
        elif command.action == "reject":
            payout.reject(processed_by=command.processed_by, notes=command.notes)
        elif command.action == "mark_paid":
            if not command.payment_reference:
                raise ValueError("payment_reference is required for mark_paid")
            payout.mark_paid(payment_reference=command.payment_reference)
            self.commission_repo.mark_confirmed_as_paid_for_reseller(payout.reseller_id)
        else:
            raise ValueError(f"Unknown action: {command.action}")

        self.payout_repo.save(payout)
