import logging
from dataclasses import dataclass
from typing import Optional

from core.email import EmailServiceInterface, send_magic_link_email
from core.stripe_client import StripeClient
from src.auth_bc.magic_link.domain.entities import MagicLink
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.ports import MagicLinkWriter, UserWriter
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.repository import CompanyRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler

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
class CreateCompanyCommand(Command):
    name: str
    email_domains: list[str]
    admin_email: Optional[str] = None
    id: Optional[str] = None


class CreateCompanyCommandHandler(CommandHandler[CreateCompanyCommand]):
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        user_repo: UserWriter,
        magic_link_repo: MagicLinkWriter,
        email_service: EmailServiceInterface,
        stripe_client: StripeClient,
    ):
        self.company_repo = company_repo
        self.user_repo = user_repo
        self.magic_link_repo = magic_link_repo
        self.email_service = email_service
        self.stripe_client = stripe_client

    def handle(self, command: CreateCompanyCommand) -> None:
        # Check name uniqueness
        existing = self.company_repo.find_by_name(command.name)
        if existing:
            raise CompanyNameExistsError("Company with this name already exists")

        # Validate + normalize domains early so uniqueness checks are canonical
        company = Company.create(
            name=command.name, email_domains=command.email_domains, id=command.id,
        )

        # Check domain uniqueness — allow reclaiming if the owning company has no confirmed users
        for domain in company.email_domains:
            owner_id = self.company_repo.find_domain(domain)
            if owner_id:
                if self.user_repo.has_any_verified_user_in_company(owner_id):
                    raise DomainAlreadyTakenError(domain)
                # No confirmed users: delete the unconfirmed company so this registration can proceed
                logger.info(
                    "Reclaiming domain '%s' from unconfirmed company %s", domain, owner_id
                )
                self.user_repo.delete_by_company(owner_id)
                self.company_repo.delete(owner_id)

        self.company_repo.save(company)
        self.company_repo.save_domains(company.id, company.email_domains)

        # Create Stripe customer (no-op if open_source_mode=True)
        customer_id = self.stripe_client.create_customer(
            name=company.name,
            email=command.admin_email or "",
            metadata={"company_id": company.id},
        )
        company.stripe_customer_id = customer_id
        self.company_repo.save(company)

        # Handle initial admin
        if command.admin_email:
            email = command.admin_email.lower().strip()
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError("User with this email already exists")

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
