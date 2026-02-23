import logging
from dataclasses import dataclass

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class OverrideCompanyPlanCommand(Command):
    company_id: str
    new_plan: PlanTier


class OverrideCompanyPlanCommandHandler(CommandHandler[OverrideCompanyPlanCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: OverrideCompanyPlanCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        company.plan = command.new_plan
        company.billing_status = BillingStatus.ACTIVE
        self.company_repo.save(company)
        logger.info("Plan overridden: company=%s new_plan=%s", command.company_id, command.new_plan)
