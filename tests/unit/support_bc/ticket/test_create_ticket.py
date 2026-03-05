from unittest.mock import MagicMock

from src.support_bc.ticket.application.commands.create_ticket import (
    CreateTicketCommand,
    CreateTicketCommandHandler,
)
from src.support_bc.ticket.domain.enums import TicketPriority, TicketStatus


class TestCreateTicketCommandHandler:
    def setup_method(self):
        self.ticket_repo = MagicMock()
        self.handler = CreateTicketCommandHandler(ticket_repo=self.ticket_repo)

    def test_creates_ticket_and_stores_result(self):
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            CreateTicketCommand(
                company_id="company-1",
                created_by="user-1",
                category="bug_report",
                subject="Test bug",
                description="Something is broken",
            )
        )

        assert self.handler.created_ticket is not None
        assert self.handler.created_ticket.subject == "Test bug"
        assert self.handler.created_ticket.status == TicketStatus.OPEN
        assert self.handler.created_ticket.priority == TicketPriority.MEDIUM
        self.ticket_repo.save.assert_called_once()

    def test_passes_ai_conversation_summary(self):
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            CreateTicketCommand(
                company_id="c1",
                created_by="u1",
                category="how_to",
                subject="Help needed",
                description="Can't figure out",
                ai_conversation_summary="AI tried but failed",
            )
        )

        saved_ticket = self.ticket_repo.save.call_args[0][0]
        assert saved_ticket.ai_conversation_summary == "AI tried but failed"
