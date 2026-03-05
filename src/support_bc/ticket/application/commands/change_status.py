from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.enums import TicketStatus
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class ChangeTicketStatusCommand(Command):
    ticket_id: str
    new_status: str


class ChangeTicketStatusCommandHandler(CommandHandler[ChangeTicketStatusCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ChangeTicketStatusCommand) -> None:
        ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.change_status(TicketStatus(command.new_status))
        self.ticket_repo.save(ticket)
