from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.enums import TicketPriority
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class ChangeTicketPriorityCommand(Command):
    ticket_id: str
    new_priority: str


class ChangeTicketPriorityCommandHandler(
    CommandHandler[ChangeTicketPriorityCommand]
):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ChangeTicketPriorityCommand) -> None:
        ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.change_priority(TicketPriority(command.new_priority))
        self.ticket_repo.save(ticket)
