import logging
import secrets
from dataclasses import dataclass
from typing import Optional

import ulid
from sqlalchemy.orm import Session

from core.password import PasswordService
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.commands.create_company import (
    CreateCompanyCommand as CreateCompanyCmd,
    CreateCompanyCommandHandler,
)
from src.company_bc.company.application.ports import UserWriter
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.application.dtos import DemoAccountCreatedDto
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.domain.exceptions import DemoAccountLimitExceededException
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerSuspendedException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface

logger = logging.getLogger(__name__)

DEMO_LIMIT = 5


@dataclass
class CreateDemoAccountCommand(Command):
    id: str
    reseller_id: str
    company_name: str
    admin_email: Optional[str] = None


class CreateDemoAccountCommandHandler(CommandHandler[CreateDemoAccountCommand]):
    def __init__(
        self,
        client_repo: ResellerClientRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
        company_handler: CreateCompanyCommandHandler,
        user_repo: UserWriter,
        session: Session,
    ):
        self.client_repo = client_repo
        self.reseller_repo = reseller_repo
        self.company_handler = company_handler
        self.user_repo = user_repo
        self.session = session
        self._result: DemoAccountCreatedDto | None = None

    @property
    def result(self) -> DemoAccountCreatedDto | None:
        return self._result

    def handle(self, command: CreateDemoAccountCommand) -> None:
        # Validate reseller exists and is ACTIVE
        reseller = self.reseller_repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)
        if reseller.status == ResellerStatus.SUSPENDED:
            raise ResellerSuspendedException(command.reseller_id)

        # Check active demo count < limit
        active_demos = self.client_repo.count_active_demos_by_reseller_id(command.reseller_id)
        if active_demos >= DEMO_LIMIT:
            raise DemoAccountLimitExceededException(command.reseller_id, DEMO_LIMIT)

        # Generate company ID and synthetic domain
        company_id = str(ulid.new())
        demo_slug = str(ulid.new()).lower()
        demo_domain = f"demo-{demo_slug}.dsm.local"
        company_name = f"{command.company_name} (Demo)"

        # Create Company via CreateCompanyCommandHandler
        self.company_handler.handle(CreateCompanyCmd(
            name=company_name,
            email_domains=[demo_domain],
            admin_email=None,
            id=company_id,
            is_demo=True,
        ))

        # Create admin user with generated password
        admin_email = command.admin_email or f"admin@{demo_domain}"
        plain_password = secrets.token_urlsafe(12)
        hashed_password = PasswordService.hash_password(plain_password)

        admin_user = User.create(
            email=admin_email,
            role=UserRole.ADMIN,
            company_id=company_id,
            name="Demo Admin",
        )
        admin_user.set_password_hash(hashed_password)
        self.user_repo.save(admin_user)

        # Populate demo data (departments, assets, requests, etc.)
        from scripts.seed_demo_data import seed_company_data
        seed_company_data(self.session, company_id, command.company_name)

        # Create ResellerClient
        client = ResellerClient.create(
            reseller_id=command.reseller_id,
            company_id=company_id,
            source=ClientSource.MANUAL,
            is_demo=True,
            id=command.id,
        )
        self.client_repo.save(client)

        # Store result for router to read
        self._result = DemoAccountCreatedDto(
            client_id=client.id,
            company_id=company_id,
            company_name=company_name,
            admin_email=admin_email,
            admin_password=plain_password,
        )

        logger.info(
            "Demo account created: client=%s, company=%s, reseller=%s",
            client.id, company_id, command.reseller_id,
        )
