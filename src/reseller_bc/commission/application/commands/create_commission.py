from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class CreateCommissionCommand(Command):
    stripe_invoice_id: str
    company_id: str
    payment_amount_cents: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CreateCommissionCommandHandler(CommandHandler[CreateCommissionCommand]):
    def __init__(
        self,
        commission_repo: ResellerCommissionRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        self.commission_repo = commission_repo
        self.client_repo = client_repo
        self.reseller_repo = reseller_repo

    def handle(self, command: CreateCommissionCommand) -> None:
        # 1. Find ResellerClient by company_id
        client = self.client_repo.find_by_company_id(command.company_id)
        if client is None:
            return  # Not a reseller client — skip

        # 2. Skip demo accounts
        if client.is_demo:
            return

        # 3. Idempotency: check if commission already exists for this invoice
        existing = self.commission_repo.find_by_stripe_invoice_id(command.stripe_invoice_id)
        if existing is not None:
            return  # Already processed

        # 4. Get reseller for commission_pct
        reseller = self.reseller_repo.get_by_id(client.reseller_id)
        if reseller is None:
            return  # Orphaned client — skip

        # 5. Create commission
        commission = ResellerCommission.create(
            reseller_id=reseller.id,
            reseller_client_id=client.id,
            company_id=command.company_id,
            payment_amount_cents=command.payment_amount_cents,
            commission_pct=reseller.commission_pct,
            stripe_invoice_id=command.stripe_invoice_id,
            period_start=command.period_start,
            period_end=command.period_end,
        )
        self.commission_repo.save(commission)
