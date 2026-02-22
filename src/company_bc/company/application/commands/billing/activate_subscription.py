import logging
from dataclasses import dataclass
from datetime import datetime

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class ActivateSubscriptionCommand(Command):
    stripe_customer_id: str
    stripe_subscription_id: str
    plan: PlanTier
    current_period_end: datetime


class ActivateSubscriptionCommandHandler(CommandHandler[ActivateSubscriptionCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: ActivateSubscriptionCommand) -> None:
        company = self.company_repo.find_by_stripe_customer_id(command.stripe_customer_id)
        if not company:
            raise CompanyNotFoundError(
                f"No company found for stripe_customer_id={command.stripe_customer_id}"
            )
        company.apply_plan_change(
            command.plan, command.stripe_subscription_id, command.current_period_end
        )
        company.set_billing_status(BillingStatus.ACTIVE)
        self.company_repo.save(company)
        logger.info(
            "Subscription activated: company=%s plan=%s sub=%s",
            company.id,
            command.plan,
            command.stripe_subscription_id,
        )
