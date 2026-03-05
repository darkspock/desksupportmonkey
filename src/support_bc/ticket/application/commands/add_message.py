from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.entities import TicketMessage
from src.support_bc.ticket.domain.enums import TicketStatus
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketNotFoundError,
)
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class AddTicketMessageCommand(Command):
    ticket_id: str
    author_id: str
    body: str
    is_from_platform: bool = False
    company_id: Optional[str] = None  # None for super admin


class AddTicketMessageCommandHandler(CommandHandler[AddTicketMessageCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: AddTicketMessageCommand) -> None:
        if command.company_id:
            ticket = self.ticket_repo.find_by_id(
                command.ticket_id, command.company_id
            )
        else:
            ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)

        if not ticket:
            raise TicketNotFoundError("Ticket not found")

        if ticket.status == TicketStatus.CLOSED:
            raise InvalidTicketTransitionError(
                "Cannot add messages to a closed ticket"
            )

        # Auto-transition based on who is messaging
        if command.is_from_platform and ticket.status == TicketStatus.OPEN:
            ticket.change_status(TicketStatus.IN_PROGRESS)
        elif (
            not command.is_from_platform
            and ticket.status == TicketStatus.WAITING_ON_CUSTOMER
        ):
            ticket.change_status(TicketStatus.IN_PROGRESS)

        self.ticket_repo.save(ticket)

        message = TicketMessage.create(
            ticket_id=command.ticket_id,
            author_id=command.author_id,
            body=command.body,
            is_from_platform=command.is_from_platform,
        )
        self.ticket_repo.save_message(message)
