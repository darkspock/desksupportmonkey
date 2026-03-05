"""Command to attribute a newly registered company to a reseller via referral code."""
import logging
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

logger = logging.getLogger(__name__)


@dataclass
class CreateReferralAttributionCommand(Command):
    referral_code: str
    company_id: str


class CreateReferralAttributionCommandHandler(CommandHandler[CreateReferralAttributionCommand]):
    def __init__(
        self,
        reseller_repo: ResellerRepository,
        client_repo: ResellerClientRepository,
    ):
        self.reseller_repo = reseller_repo
        self.client_repo = client_repo

    def handle(self, command: CreateReferralAttributionCommand) -> None:
        # 1. Lookup reseller by referral code
        reseller = self.reseller_repo.find_by_referral_code(command.referral_code)
        if reseller is None:
            return  # Invalid code — fail silently

        # 2. Only active resellers get attribution
        if reseller.status != ResellerStatus.ACTIVE:
            return  # Inactive reseller — fail silently

        # 3. First-wins: don't re-attribute an already-linked company
        existing = self.client_repo.find_by_company_id(command.company_id)
        if existing is not None:
            return  # Already attributed — skip

        # 4. Create referral client record
        client = ResellerClient.create(
            reseller_id=reseller.id,
            company_id=command.company_id,
            source=ClientSource.REFERRAL,
            is_demo=False,
        )
        self.client_repo.save(client)

        logger.info(
            "Referral attribution: company=%s -> reseller=%s (code=%s)",
            command.company_id, reseller.id, command.referral_code,
        )
