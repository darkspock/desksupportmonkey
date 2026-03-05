import logging
from dataclasses import dataclass
from typing import Optional

from core.stripe_client import StripeClient
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class NotDemoAccountError(Exception):
    pass


class CompanyNotFoundError(Exception):
    pass


@dataclass
class ActivateDemoCommand(Command):
    company_id: str
    company_name: Optional[str] = None
    email_domains: Optional[list[str]] = None
    keep_demo_data: bool = True


class ActivateDemoCommandHandler(CommandHandler[ActivateDemoCommand]):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        stripe_client: StripeClient,
    ):
        self.company_repo = company_repo
        self.stripe_client = stripe_client

    def handle(self, command: ActivateDemoCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError(f"Company {command.company_id} not found")

        if company.plan != PlanTier.DEMO:
            raise NotDemoAccountError("Company is not a demo account")

        # Activate from demo → FREE plan with trial
        company.activate_from_demo(
            name=command.company_name,
            email_domains=command.email_domains,
        )

        # Update email domains in the domains table if changed
        if command.email_domains:
            self.company_repo.save_domains(company.id, company.email_domains)

        # Create Stripe customer (skipped during demo creation)
        customer_id = self.stripe_client.create_customer(
            name=company.name,
            email="",
            metadata={"company_id": company.id},
        )
        company.stripe_customer_id = customer_id

        self.company_repo.save(company)

        logger.info(
            "Demo company activated: %s (id=%s), plan=%s",
            company.name, company.id, company.plan.value,
        )
