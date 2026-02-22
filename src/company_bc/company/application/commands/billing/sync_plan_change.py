import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class SyncPlanChangeCommand(Command):
    stripe_customer_id: str
    new_plan: PlanTier
    subscription_status: str
    current_period_end: datetime
    pending_downgrade_plan: Optional[PlanTier]


class SyncPlanChangeCommandHandler(CommandHandler[SyncPlanChangeCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: SyncPlanChangeCommand) -> None:
        company = self.company_repo.find_by_stripe_customer_id(command.stripe_customer_id)
        if not company:
            raise CompanyNotFoundError(
                f"No company found for stripe_customer_id={command.stripe_customer_id}"
            )
        if command.subscription_status == "past_due":
            company.enter_grace_period()
        else:
            company.plan = command.new_plan
            company.current_period_end = command.current_period_end
            company.pending_downgrade_plan = command.pending_downgrade_plan
            if company.billing_status in (BillingStatus.GRACE_PERIOD, BillingStatus.SUSPENDED):
                company.billing_status = BillingStatus.ACTIVE
                company.grace_period_started_at = None
        self.company_repo.save(company)
        logger.info(
            "Plan synced: company=%s plan=%s status=%s",
            company.id,
            command.new_plan,
            command.subscription_status,
        )
