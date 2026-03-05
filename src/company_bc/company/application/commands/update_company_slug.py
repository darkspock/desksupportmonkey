from dataclasses import dataclass

from src.company_bc.company.domain.entities import Company, SlugAlreadyTakenError
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class CompanyNotFoundError(Exception):
    pass


@dataclass
class UpdateCompanySlugCommand(Command):
    company_id: str
    slug: str


class UpdateCompanySlugCommandHandler(CommandHandler[UpdateCompanySlugCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: UpdateCompanySlugCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError(command.company_id)
        Company.validate_slug(command.slug)
        if self.company_repo.slug_exists(command.slug, exclude_company_id=command.company_id):
            raise SlugAlreadyTakenError(command.slug)
        company.update_slug(command.slug)
        self.company_repo.save(company)
