import logging
from dataclasses import dataclass

from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


@dataclass
class RevokeComplimentaryPlanCommand(Command):
    company_id: str


class RevokeComplimentaryPlanCommandHandler(CommandHandler[RevokeComplimentaryPlanCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface) -> None:
        self.company_repo = company_repo

    def handle(self, command: RevokeComplimentaryPlanCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        if not company.complimentary:
            raise ValueError("Company is not on complimentary plan")
        company.revoke_complimentary()
        self.company_repo.save(company)
        logger.info("Complimentary plan revoked: company=%s", command.company_id)
