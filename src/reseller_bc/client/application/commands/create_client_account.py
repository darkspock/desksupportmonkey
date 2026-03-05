import logging
from dataclasses import dataclass

import ulid

from src.company_bc.company.application.commands.create_company import (
    CreateCompanyCommand as CreateCompanyCmd,
    CreateCompanyCommandHandler,
)
from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.domain.exceptions import CompanyAlreadyLinkedToResellerException
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerSuspendedException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface

logger = logging.getLogger(__name__)


@dataclass
class CreateClientAccountCommand(Command):
    id: str
    reseller_id: str
    company_name: str
    admin_email: str


class CreateClientAccountCommandHandler(CommandHandler[CreateClientAccountCommand]):
    def __init__(
        self,
        client_repo: ResellerClientRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
        company_handler: CreateCompanyCommandHandler,
    ):
        self.client_repo = client_repo
        self.reseller_repo = reseller_repo
        self.company_handler = company_handler

    def handle(self, command: CreateClientAccountCommand) -> None:
        # Validate reseller exists and is ACTIVE
        reseller = self.reseller_repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)
        if reseller.status == ResellerStatus.SUSPENDED:
            raise ResellerSuspendedException(command.reseller_id)

        # Derive email domain from admin_email
        domain = command.admin_email.split("@")[1].lower().strip()

        # Create Company via CreateCompanyCommandHandler (sends magic link to admin)
        company_id = str(ulid.new())
        self.company_handler.handle(CreateCompanyCmd(
            name=command.company_name,
            email_domains=[domain],
            admin_email=command.admin_email,
            id=company_id,
        ))

        # Create ResellerClient
        client = ResellerClient.create(
            reseller_id=command.reseller_id,
            company_id=company_id,
            source=ClientSource.MANUAL,
            is_demo=False,
            id=command.id,
        )
        self.client_repo.save(client)

        logger.info(
            "Client account created: client=%s, company=%s, reseller=%s",
            client.id, company_id, command.reseller_id,
        )
