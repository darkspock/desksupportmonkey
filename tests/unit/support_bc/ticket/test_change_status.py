from unittest.mock import MagicMock

import pytest

from src.support_bc.ticket.application.commands.change_status import (
    ChangeTicketStatusCommand,
    ChangeTicketStatusCommandHandler,
)
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketNotFoundError,
)


def _make_ticket(status=TicketStatus.OPEN):
    return SupportTicket(
        id="t1",
        reference="SUP-0001",
        company_id="c1",
        created_by="u1",
        category=TicketCategory.BUG_REPORT,
        subject="Test",
        description="Test desc",
        status=status,
        priority=TicketPriority.MEDIUM,
    )


class TestChangeTicketStatusCommandHandler:
    def setup_method(self):
        self.ticket_repo = MagicMock()
        self.handler = ChangeTicketStatusCommandHandler(ticket_repo=self.ticket_repo)

    def test_valid_transition(self):
        ticket = _make_ticket(TicketStatus.OPEN)
        self.ticket_repo.find_by_id_any_company.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            ChangeTicketStatusCommand(ticket_id="t1", new_status="in_progress")
        )

        assert ticket.status == TicketStatus.IN_PROGRESS
        self.ticket_repo.save.assert_called_once()

    def test_invalid_transition_raises(self):
        ticket = _make_ticket(TicketStatus.CLOSED)
        self.ticket_repo.find_by_id_any_company.return_value = ticket

        with pytest.raises(InvalidTicketTransitionError):
            self.handler.handle(
                ChangeTicketStatusCommand(ticket_id="t1", new_status="open")
            )

    def test_ticket_not_found_raises(self):
        self.ticket_repo.find_by_id_any_company.return_value = None

        with pytest.raises(TicketNotFoundError):
            self.handler.handle(
                ChangeTicketStatusCommand(ticket_id="nonexistent", new_status="resolved")
            )

    def test_uses_unscoped_lookup(self):
        ticket = _make_ticket(TicketStatus.OPEN)
        self.ticket_repo.find_by_id_any_company.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            ChangeTicketStatusCommand(ticket_id="t1", new_status="resolved")
        )

        self.ticket_repo.find_by_id_any_company.assert_called_once_with("t1")
