"""Unit tests for satisfaction rating — entity method + command handler."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.enums import TicketCategory, TicketPriority, TicketStatus
from src.support_bc.ticket.domain.exceptions import (
    TicketAlreadyRatedError,
    TicketRatingNotAllowedError,
)
from src.support_bc.ticket.application.commands.rate_ticket import (
    RateTicketCommand,
    RateTicketCommandHandler,
)
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError


def _make_ticket(status=TicketStatus.RESOLVED, **kwargs) -> SupportTicket:
    defaults = dict(
        id="t1",
        reference="SUP-0001",
        company_id="c1",
        created_by="u1",
        category=TicketCategory.BUG_REPORT,
        subject="Test",
        description="desc",
        status=status,
        priority=TicketPriority.MEDIUM,
        resolved_at=datetime.now(timezone.utc) if status == TicketStatus.RESOLVED else None,
    )
    defaults.update(kwargs)
    return SupportTicket(**defaults)


class TestSupportTicketRate:
    def test_rate_valid(self):
        ticket = _make_ticket()
        ticket.rate(4, "Great support!")
        assert ticket.satisfaction_rating == 4
        assert ticket.satisfaction_comment == "Great support!"
        assert ticket.rated_at is not None

    def test_rate_without_comment(self):
        ticket = _make_ticket()
        ticket.rate(5)
        assert ticket.satisfaction_rating == 5
        assert ticket.satisfaction_comment is None
        assert ticket.rated_at is not None

    def test_rate_strips_comment_whitespace(self):
        ticket = _make_ticket()
        ticket.rate(3, "  nice  ")
        assert ticket.satisfaction_comment == "nice"

    def test_rate_already_rated_raises(self):
        ticket = _make_ticket(satisfaction_rating=5, rated_at=datetime.now(timezone.utc))
        with pytest.raises(TicketAlreadyRatedError):
            ticket.rate(3)

    def test_rate_open_ticket_raises(self):
        ticket = _make_ticket(status=TicketStatus.OPEN)
        with pytest.raises(TicketRatingNotAllowedError):
            ticket.rate(4)

    def test_rate_in_progress_ticket_raises(self):
        ticket = _make_ticket(status=TicketStatus.IN_PROGRESS)
        with pytest.raises(TicketRatingNotAllowedError):
            ticket.rate(4)

    def test_rate_closed_ticket_allowed(self):
        ticket = _make_ticket(status=TicketStatus.CLOSED)
        ticket.rate(2, "Took too long")
        assert ticket.satisfaction_rating == 2

    def test_rate_out_of_range_low(self):
        ticket = _make_ticket()
        with pytest.raises(ValueError):
            ticket.rate(0)

    def test_rate_out_of_range_high(self):
        ticket = _make_ticket()
        with pytest.raises(ValueError):
            ticket.rate(6)


class TestRateTicketCommandHandler:
    def test_success(self):
        ticket = _make_ticket()
        repo = MagicMock()
        repo.find_by_id.return_value = ticket
        handler = RateTicketCommandHandler(ticket_repo=repo)

        handler.handle(RateTicketCommand(
            ticket_id="t1", company_id="c1", user_id="u1", rating=5, comment="Excellent",
        ))

        assert ticket.satisfaction_rating == 5
        repo.save.assert_called_once_with(ticket)

    def test_ticket_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = RateTicketCommandHandler(ticket_repo=repo)

        with pytest.raises(TicketNotFoundError):
            handler.handle(RateTicketCommand(
                ticket_id="t1", company_id="c1", user_id="u1", rating=5,
            ))

    def test_wrong_user_raises(self):
        ticket = _make_ticket(created_by="u1")
        repo = MagicMock()
        repo.find_by_id.return_value = ticket
        handler = RateTicketCommandHandler(ticket_repo=repo)

        with pytest.raises(TicketNotFoundError):
            handler.handle(RateTicketCommand(
                ticket_id="t1", company_id="c1", user_id="u-other", rating=5,
            ))

    def test_already_rated_raises(self):
        ticket = _make_ticket(satisfaction_rating=5, rated_at=datetime.now(timezone.utc))
        repo = MagicMock()
        repo.find_by_id.return_value = ticket
        handler = RateTicketCommandHandler(ticket_repo=repo)

        with pytest.raises(TicketAlreadyRatedError):
            handler.handle(RateTicketCommand(
                ticket_id="t1", company_id="c1", user_id="u1", rating=3,
            ))
