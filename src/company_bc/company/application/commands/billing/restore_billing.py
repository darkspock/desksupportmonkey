import logging
from dataclasses import dataclass

from src.company_bc.company.domain.billing_enums import BillingStatus
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class RestoreBillingCommand(Command):
    stripe_customer_id: str


class RestoreBillingCommandHandler(CommandHandler[RestoreBillingCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: RestoreBillingCommand) -> None:
        company = self.company_repo.find_by_stripe_customer_id(command.stripe_customer_id)
        if not company:
            raise CompanyNotFoundError(
                f"No company found for stripe_customer_id={command.stripe_customer_id}"
            )
        if company.billing_status in (BillingStatus.GRACE_PERIOD, BillingStatus.SUSPENDED):
            company.restore_billing()
            self.company_repo.save(company)
            logger.info("Billing restored: company=%s → ACTIVE", company.id)
        else:
            logger.debug(
                "Billing restore skipped: company=%s status=%s", company.id, company.billing_status
            )
