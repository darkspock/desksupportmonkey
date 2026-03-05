from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class ReopenTicketCommand(Command):
    ticket_id: str
    company_id: str


class ReopenTicketCommandHandler(CommandHandler[ReopenTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ReopenTicketCommand) -> None:
        ticket = self.ticket_repo.find_by_id(
            command.ticket_id, command.company_id
        )
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.reopen()  # Validates status + 7-day window
        self.ticket_repo.save(ticket)
