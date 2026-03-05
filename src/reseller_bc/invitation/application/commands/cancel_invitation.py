"""Command to cancel a pending reseller invitation."""
import logging
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.invitation.domain.repository import ResellerInvitationRepositoryInterface

logger = logging.getLogger(__name__)


@dataclass
class CancelInvitationCommand(Command):
    invitation_id: str
    reseller_id: str


class CancelInvitationCommandHandler(CommandHandler[CancelInvitationCommand]):
    def __init__(self, invitation_repo: ResellerInvitationRepositoryInterface):
        self.invitation_repo = invitation_repo

    def handle(self, command: CancelInvitationCommand) -> None:
        result = self.invitation_repo.cancel_by_id(command.invitation_id, command.reseller_id)
        if result is None:
            logger.warning(
                "Cancel invitation failed: not found or not pending. invitation=%s reseller=%s",
                command.invitation_id, command.reseller_id,
            )
            return

        logger.info(
            "Invitation cancelled: invitation=%s reseller=%s",
            command.invitation_id, command.reseller_id,
        )
