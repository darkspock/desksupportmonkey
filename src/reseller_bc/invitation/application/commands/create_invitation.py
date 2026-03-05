"""Command to create a reseller invitation pre-claim."""
import logging
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.invitation.domain.entities import ResellerInvitation
from src.reseller_bc.invitation.domain.exceptions import (
    InvitationAlreadyExistsException,
    InvitationLimitExceededException,
)
from src.reseller_bc.invitation.domain.repository import ResellerInvitationRepositoryInterface

logger = logging.getLogger(__name__)

MAX_PENDING_INVITATIONS = 20


@dataclass
class CreateInvitationCommand(Command):
    reseller_id: str
    email: str


class CreateInvitationCommandHandler(CommandHandler[CreateInvitationCommand]):
    def __init__(self, invitation_repo: ResellerInvitationRepositoryInterface):
        self.invitation_repo = invitation_repo
        self.result: ResellerInvitation | None = None

    def handle(self, command: CreateInvitationCommand) -> None:
        email = command.email.lower().strip()

        # Check pending limit
        pending_count = self.invitation_repo.count_pending_by_reseller_id(command.reseller_id)
        if pending_count >= MAX_PENDING_INVITATIONS:
            raise InvitationLimitExceededException(command.reseller_id)

        # Check for existing pending invitation from this reseller for this email
        existing = self.invitation_repo.find_pending_by_email(email)
        if existing and existing.reseller_id == command.reseller_id:
            raise InvitationAlreadyExistsException(command.reseller_id, email)

        invitation = ResellerInvitation.create(
            reseller_id=command.reseller_id,
            email=email,
        )
        self.invitation_repo.save(invitation)
        self.result = invitation

        logger.info(
            "Invitation created: reseller=%s email=%s invitation=%s",
            command.reseller_id, email, invitation.id,
        )
