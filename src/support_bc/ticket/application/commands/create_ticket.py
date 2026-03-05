from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class CreateTicketCommand(Command):
    company_id: str
    created_by: str
    category: str
    subject: str
    description: str
    ai_conversation_summary: Optional[str] = None


class CreateTicketCommandHandler(CommandHandler[CreateTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo
        self.created_ticket: Optional[SupportTicket] = None

    def handle(self, command: CreateTicketCommand) -> None:
        ticket = SupportTicket.create(
            company_id=command.company_id,
            created_by=command.created_by,
            category=command.category,
            subject=command.subject,
            description=command.description,
            ai_conversation_summary=command.ai_conversation_summary,
        )
        self.created_ticket = self.ticket_repo.save(ticket)
