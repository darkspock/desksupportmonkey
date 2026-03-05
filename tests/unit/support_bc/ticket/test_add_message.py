from unittest.mock import MagicMock

import pytest

from src.support_bc.ticket.application.commands.add_message import (
    AddTicketMessageCommand,
    AddTicketMessageCommandHandler,
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


class TestAddTicketMessageCommandHandler:
    def setup_method(self):
        self.ticket_repo = MagicMock()
        self.handler = AddTicketMessageCommandHandler(ticket_repo=self.ticket_repo)

    def test_platform_message_on_open_transitions_to_in_progress(self):
        ticket = _make_ticket(TicketStatus.OPEN)
        self.ticket_repo.find_by_id_any_company.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            AddTicketMessageCommand(
                ticket_id="t1",
                author_id="admin-1",
                body="We're looking into this",
                is_from_platform=True,
                company_id=None,
            )
        )

        assert ticket.status == TicketStatus.IN_PROGRESS
        self.ticket_repo.save_message.assert_called_once()

    def test_customer_message_on_waiting_transitions_to_in_progress(self):
        ticket = _make_ticket(TicketStatus.WAITING_ON_CUSTOMER)
        self.ticket_repo.find_by_id.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            AddTicketMessageCommand(
                ticket_id="t1",
                author_id="u1",
                body="Here is the info you requested",
                is_from_platform=False,
                company_id="c1",
            )
        )

        assert ticket.status == TicketStatus.IN_PROGRESS
        self.ticket_repo.save_message.assert_called_once()

    def test_message_on_closed_ticket_raises(self):
        ticket = _make_ticket(TicketStatus.CLOSED)
        self.ticket_repo.find_by_id.return_value = ticket

        with pytest.raises(InvalidTicketTransitionError):
            self.handler.handle(
                AddTicketMessageCommand(
                    ticket_id="t1",
                    author_id="u1",
                    body="Hello?",
                    company_id="c1",
                )
            )

    def test_ticket_not_found_raises(self):
        self.ticket_repo.find_by_id.return_value = None

        with pytest.raises(TicketNotFoundError):
            self.handler.handle(
                AddTicketMessageCommand(
                    ticket_id="nonexistent",
                    author_id="u1",
                    body="Hello",
                    company_id="c1",
                )
            )

    def test_company_scoped_lookup_when_company_id_set(self):
        ticket = _make_ticket(TicketStatus.IN_PROGRESS)
        self.ticket_repo.find_by_id.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            AddTicketMessageCommand(
                ticket_id="t1",
                author_id="u1",
                body="Update",
                company_id="c1",
            )
        )

        self.ticket_repo.find_by_id.assert_called_once_with("t1", "c1")

    def test_unscoped_lookup_when_no_company_id(self):
        ticket = _make_ticket(TicketStatus.IN_PROGRESS)
        self.ticket_repo.find_by_id_any_company.return_value = ticket
        self.ticket_repo.save.side_effect = lambda t: t

        self.handler.handle(
            AddTicketMessageCommand(
                ticket_id="t1",
                author_id="admin-1",
                body="Platform response",
                is_from_platform=True,
                company_id=None,
            )
        )

        self.ticket_repo.find_by_id_any_company.assert_called_once_with("t1")
