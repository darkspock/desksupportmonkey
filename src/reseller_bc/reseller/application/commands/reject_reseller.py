from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerNotFoundException,
    ResellerPendingApprovalException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class RejectResellerCommand(Command):
    reseller_id: str
    reason: Optional[str] = None


class RejectResellerCommandHandler(CommandHandler[RejectResellerCommand]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, command: RejectResellerCommand) -> None:
        reseller = self.repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)

        if reseller.status != ResellerStatus.PENDING:
            raise ResellerPendingApprovalException(
                f"Cannot reject reseller with status: {reseller.status.value}"
            )

        reseller.deactivate()
        self.repo.save(reseller)

        # Send rejection email
        from core.tasks.reseller_emails import send_reseller_rejection_email

        send_reseller_rejection_email.delay(
            to_email=reseller.email,
            name=reseller.name,
            reason=command.reason,
        )
