import logging
from dataclasses import dataclass
from typing import Optional

from core.email import EmailServiceInterface, send_magic_link_email
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.magic_link.domain.repository import MagicLinkRepositoryInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface

logger = logging.getLogger(__name__)


class CompanyNameExistsError(Exception):
    pass


class DomainAlreadyTakenError(Exception):
    def __init__(self, domain: str):
        self.domain = domain
        super().__init__(f"Domain '{domain}' is already associated with another company")


class UserAlreadyExistsError(Exception):
    pass


@dataclass
class CreateCompanyCommand:
    name: str
    email_domains: list[str]
    admin_email: Optional[str] = None


class CreateCompanyCommandHandler:
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        user_repo: UserRepositoryInterface,
        magic_link_repo: MagicLinkRepositoryInterface,
        email_service: EmailServiceInterface,
    ):
        self.company_repo = company_repo
        self.user_repo = user_repo
        self.magic_link_repo = magic_link_repo
        self.email_service = email_service

    def handle(self, command: CreateCompanyCommand) -> Company:
        # Check name uniqueness
        existing = self.company_repo.find_by_name(command.name)
        if existing:
            raise CompanyNameExistsError("Company with this name already exists")

        # Check domain uniqueness
        for domain in command.email_domains:
            owner = self.company_repo.find_domain(domain.lower().strip())
            if owner:
                raise DomainAlreadyTakenError(domain)

        # Create company
        company = Company.create(name=command.name, email_domains=command.email_domains)
        self.company_repo.save(company)
        self.company_repo.save_domains(company.id, company.email_domains)

        # Handle initial admin
        if command.admin_email:
            email = command.admin_email.lower().strip()
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError("User with this email already exists")

            # Ensure admin's email domain is included in company domains
            admin_domain = email.split("@")[1] if "@" in email else None
            if admin_domain and admin_domain not in [d.lower().strip() for d in company.email_domains]:
                company.email_domains.append(admin_domain)
                self.company_repo.save_domains(company.id, company.email_domains)

            user = User.create(
                email=email,
                role=UserRole.ADMIN,
                company_id=company.id,
            )
            self.user_repo.save(user)

            magic_link = MagicLink.create(email)
            self.magic_link_repo.save(magic_link)
            send_magic_link_email(self.email_service, email, magic_link.token)
            logger.info("Initial admin %s created for company %s", email, company.name)

        logger.info("Company created: %s (id=%s)", company.name, company.id)
        return company
