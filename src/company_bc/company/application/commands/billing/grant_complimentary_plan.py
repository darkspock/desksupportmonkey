import logging
from dataclasses import dataclass

from core.stripe_client import StripeClient, StripeUnavailableError
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class GrantComplimentaryPlanCommand(Command):
    company_id: str
    plan: PlanTier


class GrantComplimentaryPlanCommandHandler(CommandHandler[GrantComplimentaryPlanCommand]):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        stripe_client: StripeClient,
    ) -> None:
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, command: GrantComplimentaryPlanCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        if company.stripe_subscription_id:
            self.stripe_client.cancel_subscription(company.stripe_subscription_id)
        company.grant_complimentary(command.plan)
        self.company_repo.save(company)
        logger.info(
            "Complimentary plan granted: company=%s plan=%s", command.company_id, command.plan
        )
