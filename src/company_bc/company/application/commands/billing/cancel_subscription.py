import logging
from dataclasses import dataclass

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class CancelSubscriptionCommand(Command):
    stripe_customer_id: str


class CancelSubscriptionCommandHandler(CommandHandler[CancelSubscriptionCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: CancelSubscriptionCommand) -> None:
        company = self.company_repo.find_by_stripe_customer_id(command.stripe_customer_id)
        if not company:
            raise CompanyNotFoundError(
                f"No company found for stripe_customer_id={command.stripe_customer_id}"
            )
        company.plan = PlanTier.FREE
        company.stripe_subscription_id = None
        company.billing_status = BillingStatus.ACTIVE
        company.pending_downgrade_plan = None
        self.company_repo.save(company)
        logger.info("Subscription cancelled: company=%s → FREE", company.id)
