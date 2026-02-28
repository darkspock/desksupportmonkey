import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.company.domain.entities import InvalidSectorError
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class CompleteOnboardingCommand(Command):
    company_id: str
    sector: Optional[str] = None


class CompleteOnboardingCommandHandler(CommandHandler[CompleteOnboardingCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: CompleteOnboardingCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        company.set_sector(command.sector)
        company.complete_onboarding()
        self.company_repo.save(company)
        logger.info("Onboarding completed for company %s", command.company_id)
