from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.support_bc.ticket.application.commands.reopen_ticket import (
    ReopenTicketCommand,
    ReopenTicketCommandHandler,
)
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from src.support_bc.ticket.domain.exceptions import (
    TicketNotFoundError,
    TicketReopenWindowExpiredError,
)


def _make_resolved_ticket(days_ago=1):
    return SupportTicket(
        id="t1",
        reference="SUP-0001",
        company_id="c1",
        created_by="u1",
        category=TicketCategory.BUG_REPORT,
        subject="Test",
        description="Test desc",
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.MEDIUM,
        resolved_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


class TestReopenTicketCommandHandler:
    def setup_method(self):
        self.ticket_repo = MagicMock()
        self.handler = ReopenTicketCommandHandler(ticket_repo=self.ticket_repo)

    def test_reopen_within_window(self):
        ticket = _make_resolved_ticket(days_ago=3)
        self.ticket_repo.find_by_id.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            ReopenTicketCommand(ticket_id="t1", company_id="c1")
        )

        assert ticket.status == TicketStatus.OPEN
        assert ticket.resolved_at is None
        self.ticket_repo.save.assert_called_once()

    def test_reopen_after_window_raises(self):
        ticket = _make_resolved_ticket(days_ago=8)
        self.ticket_repo.find_by_id.return_value = ticket

        with pytest.raises(TicketReopenWindowExpiredError):
            self.handler.handle(
                ReopenTicketCommand(ticket_id="t1", company_id="c1")
            )

    def test_ticket_not_found_raises(self):
        self.ticket_repo.find_by_id.return_value = None

        with pytest.raises(TicketNotFoundError):
            self.handler.handle(
                ReopenTicketCommand(ticket_id="nonexistent", company_id="c1")
            )
