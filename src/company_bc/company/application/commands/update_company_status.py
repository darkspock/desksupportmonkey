import logging
from dataclasses import dataclass

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class UpdateCompanyStatusCommand(Command):
    company_id: str
    new_status: str


class UpdateCompanyStatusCommandHandler(CommandHandler[UpdateCompanyStatusCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: UpdateCompanyStatusCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")

        new_status = CompanyStatus(command.new_status)  # raises ValueError if invalid
        old_status = company.status
        company.change_status(new_status)  # raises InvalidStatusTransitionError
        self.company_repo.save(company)

        logger.info(
            "Company %s status changed: %s -> %s",
            company.id,
            old_status.value,
            new_status.value,
        )
