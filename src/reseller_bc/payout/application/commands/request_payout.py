from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.payout.domain.exceptions import (
    InsufficientBalanceException,
    PayoutAlreadyPendingException,
)
from src.reseller_bc.payout.domain.repository import ResellerPayoutRepositoryInterface
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerSuspendedException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class RequestPayoutCommand(Command):
    id: str
    reseller_id: str


class RequestPayoutCommandHandler(CommandHandler[RequestPayoutCommand]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        commission_repo: ResellerCommissionRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        self.payout_repo = payout_repo
        self.commission_repo = commission_repo
        self.reseller_repo = reseller_repo

    def handle(self, command: RequestPayoutCommand) -> None:
        reseller = self.reseller_repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)
        if reseller.status == ResellerStatus.SUSPENDED:
            raise ResellerSuspendedException(command.reseller_id)

        # Guard: one active payout at a time
        active = self.payout_repo.find_active_by_reseller_id(command.reseller_id)
        if active is not None:
            raise PayoutAlreadyPendingException(command.reseller_id)

        # Calculate available balance
        confirmed = self.commission_repo.sum_confirmed_by_reseller_id(command.reseller_id)
        paid = self.commission_repo.sum_paid_by_reseller_id(command.reseller_id)
        clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(command.reseller_id)
        balance = confirmed - paid + clawbacks

        if balance < reseller.min_payout_cents:
            raise InsufficientBalanceException(balance, reseller.min_payout_cents)

        payout = ResellerPayout.create(
            reseller_id=command.reseller_id,
            amount_cents=balance,
            id=command.id,
        )
        self.payout_repo.save(payout)
