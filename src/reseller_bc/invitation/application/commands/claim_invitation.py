"""Command to claim a pending invitation during registration."""
import logging
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.invitation.domain.enums import InvitationStatus
from src.reseller_bc.invitation.domain.repository import ResellerInvitationRepositoryInterface

logger = logging.getLogger(__name__)


@dataclass
class ClaimInvitationCommand(Command):
    email: str
    company_id: str


class ClaimInvitationCommandHandler(CommandHandler[ClaimInvitationCommand]):
    def __init__(
        self,
        invitation_repo: ResellerInvitationRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
    ):
        self.invitation_repo = invitation_repo
        self.client_repo = client_repo

    def handle(self, command: ClaimInvitationCommand) -> None:
        email = command.email.lower().strip()

        # Find first pending, non-expired invitation for this email
        invitation = self.invitation_repo.find_pending_by_email(email)
        if invitation is None:
            return  # No matching invitation — skip silently

        # Don't re-attribute an already-linked company
        existing_client = self.client_repo.find_by_company_id(command.company_id)
        if existing_client is not None:
            return  # Already attributed — skip

        # Create reseller client with INVITATION source
        client = ResellerClient.create(
            reseller_id=invitation.reseller_id,
            company_id=command.company_id,
            source=ClientSource.INVITATION,
            is_demo=False,
        )
        self.client_repo.save(client)

        # Mark invitation as attributed
        invitation.status = InvitationStatus.ATTRIBUTED
        self.invitation_repo.save(invitation)

        logger.info(
            "Invitation claimed: email=%s company=%s -> reseller=%s (invitation=%s)",
            email, command.company_id, invitation.reseller_id, invitation.id,
        )
