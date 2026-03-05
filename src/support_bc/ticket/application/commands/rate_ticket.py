from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class RateTicketCommand(Command):
    ticket_id: str
    company_id: str
    user_id: str
    rating: int
    comment: Optional[str] = None


class RateTicketCommandHandler(CommandHandler[RateTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: RateTicketCommand) -> None:
        ticket = self.ticket_repo.find_by_id(command.ticket_id, command.company_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        if ticket.created_by != command.user_id:
            raise TicketNotFoundError("Ticket not found")
        ticket.rate(command.rating, command.comment)
        self.ticket_repo.save(ticket)
