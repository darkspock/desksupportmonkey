import logging
from dataclasses import dataclass
from typing import Optional

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

logger = logging.getLogger(__name__)


class CompanyNotFoundError(Exception):
    pass


class CompanyNameExistsError(Exception):
    pass


class DomainAlreadyTakenError(Exception):
    def __init__(self, domain: str):
        self.domain = domain
        super().__init__(f"Domain '{domain}' is already associated with another company")


@dataclass
class UpdateCompanyCommand(Command):
    company_id: str
    name: Optional[str] = None
    email_domains: Optional[list[str]] = None


class UpdateCompanyCommandHandler(CommandHandler[UpdateCompanyCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: UpdateCompanyCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError("Company not found")
        normalized_domains: Optional[list[str]] = None

        # Check name uniqueness (exclude self)
        if command.name and command.name.strip().lower() != company.name.lower():
            existing = self.company_repo.find_by_name(command.name)
            if existing and existing.id != company.id:
                raise CompanyNameExistsError("Company with this name already exists")

        # Check domain uniqueness (exclude own domains)
        if command.email_domains is not None:
            normalized_domains = Company.create(
                name=company.name,
                email_domains=command.email_domains,
                id=company.id,
            ).email_domains
            for domain in normalized_domains:
                owner = self.company_repo.find_domain(domain)
                if owner and owner != company.id:
                    raise DomainAlreadyTakenError(domain)

        # Update entity
        company.update(name=command.name, email_domains=normalized_domains)
        self.company_repo.save(company)

        if command.email_domains is not None:
            self.company_repo.save_domains(company.id, company.email_domains)

        logger.info("Company updated: %s (id=%s)", company.name, company.id)
