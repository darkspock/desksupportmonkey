from datetime import datetime, timedelta, timezone

import pytest

from src.support_bc.ticket.domain.entities import SupportTicket, TicketMessage
from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketReopenWindowExpiredError,
)


class TestSupportTicketCreate:
    def test_create_with_valid_input(self):
        ticket = SupportTicket.create(
            company_id="company-1",
            created_by="user-1",
            category="bug_report",
            subject="Test subject",
            description="Test description",
        )
        assert ticket.company_id == "company-1"
        assert ticket.created_by == "user-1"
        assert ticket.category == TicketCategory.BUG_REPORT
        assert ticket.subject == "Test subject"
        assert ticket.description == "Test description"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.MEDIUM
        assert ticket.reference == ""
        assert ticket.ai_conversation_summary is None

    def test_create_strips_whitespace(self):
        ticket = SupportTicket.create(
            company_id="c1",
            created_by="u1",
            category="billing",
            subject="  Padded subject  ",
            description="  Padded desc  ",
        )
        assert ticket.subject == "Padded subject"
        assert ticket.description == "Padded desc"

    def test_create_with_empty_subject_raises(self):
        with pytest.raises(ValueError, match="Subject is required"):
            SupportTicket.create(
                company_id="c1",
                created_by="u1",
                category="billing",
                subject="",
                description="desc",
            )

    def test_create_with_whitespace_only_subject_raises(self):
        with pytest.raises(ValueError, match="Subject is required"):
            SupportTicket.create(
                company_id="c1",
                created_by="u1",
                category="billing",
                subject="   ",
                description="desc",
            )

    def test_create_with_empty_description_raises(self):
        with pytest.raises(ValueError, match="Description is required"):
            SupportTicket.create(
                company_id="c1",
                created_by="u1",
                category="billing",
                subject="sub",
                description="",
            )

    def test_create_with_ai_conversation_summary(self):
        ticket = SupportTicket.create(
            company_id="c1",
            created_by="u1",
            category="how_to",
            subject="Help",
            description="Need help",
            ai_conversation_summary="AI tried to help but could not",
        )
        assert ticket.ai_conversation_summary == "AI tried to help but could not"


class TestSupportTicketChangeStatus:
    def _make_ticket(self, status=TicketStatus.OPEN):
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

    def test_open_to_in_progress(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        ticket.change_status(TicketStatus.IN_PROGRESS)
        assert ticket.status == TicketStatus.IN_PROGRESS

    def test_open_to_resolved(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        ticket.change_status(TicketStatus.RESOLVED)
        assert ticket.status == TicketStatus.RESOLVED
        assert ticket.resolved_at is not None

    def test_open_to_closed(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        ticket.change_status(TicketStatus.CLOSED)
        assert ticket.status == TicketStatus.CLOSED
        assert ticket.closed_at is not None

    def test_in_progress_to_waiting(self):
        ticket = self._make_ticket(TicketStatus.IN_PROGRESS)
        ticket.change_status(TicketStatus.WAITING_ON_CUSTOMER)
        assert ticket.status == TicketStatus.WAITING_ON_CUSTOMER

    def test_in_progress_to_resolved(self):
        ticket = self._make_ticket(TicketStatus.IN_PROGRESS)
        ticket.change_status(TicketStatus.RESOLVED)
        assert ticket.status == TicketStatus.RESOLVED

    def test_waiting_to_in_progress(self):
        ticket = self._make_ticket(TicketStatus.WAITING_ON_CUSTOMER)
        ticket.change_status(TicketStatus.IN_PROGRESS)
        assert ticket.status == TicketStatus.IN_PROGRESS

    def test_resolved_to_closed(self):
        ticket = self._make_ticket(TicketStatus.RESOLVED)
        ticket.change_status(TicketStatus.CLOSED)
        assert ticket.status == TicketStatus.CLOSED

    def test_invalid_transition_raises(self):
        ticket = self._make_ticket(TicketStatus.CLOSED)
        with pytest.raises(InvalidTicketTransitionError):
            ticket.change_status(TicketStatus.OPEN)

    def test_open_to_waiting_invalid(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        with pytest.raises(InvalidTicketTransitionError):
            ticket.change_status(TicketStatus.WAITING_ON_CUSTOMER)

    def test_resolved_sets_resolved_at(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        ticket.change_status(TicketStatus.RESOLVED)
        assert ticket.resolved_at is not None

    def test_closed_sets_closed_at(self):
        ticket = self._make_ticket(TicketStatus.OPEN)
        ticket.change_status(TicketStatus.CLOSED)
        assert ticket.closed_at is not None


class TestSupportTicketReopen:
    def _make_resolved_ticket(self, days_ago=1):
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

    def test_reopen_within_window(self):
        ticket = self._make_resolved_ticket(days_ago=3)
        ticket.reopen()
        assert ticket.status == TicketStatus.OPEN
        assert ticket.resolved_at is None

    def test_reopen_after_window_raises(self):
        ticket = self._make_resolved_ticket(days_ago=8)
        with pytest.raises(TicketReopenWindowExpiredError):
            ticket.reopen()

    def test_reopen_non_resolved_raises(self):
        ticket = SupportTicket(
            id="t1",
            reference="SUP-0001",
            company_id="c1",
            created_by="u1",
            category=TicketCategory.BUG_REPORT,
            subject="Test",
            description="Test desc",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
        )
        with pytest.raises(InvalidTicketTransitionError):
            ticket.reopen()


class TestSupportTicketChangePriority:
    def test_change_priority(self):
        ticket = SupportTicket(
            id="t1",
            reference="SUP-0001",
            company_id="c1",
            created_by="u1",
            category=TicketCategory.BUG_REPORT,
            subject="Test",
            description="Test desc",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
        )
        ticket.change_priority(TicketPriority.URGENT)
        assert ticket.priority == TicketPriority.URGENT


class TestTicketMessage:
    def test_create_with_valid_input(self):
        msg = TicketMessage.create(
            ticket_id="t1",
            author_id="u1",
            body="Hello, I need help",
        )
        assert msg.ticket_id == "t1"
        assert msg.author_id == "u1"
        assert msg.body == "Hello, I need help"
        assert msg.is_from_platform is False
        assert msg.id is not None

    def test_create_platform_message(self):
        msg = TicketMessage.create(
            ticket_id="t1",
            author_id="admin-1",
            body="We're looking into it",
            is_from_platform=True,
        )
        assert msg.is_from_platform is True

    def test_create_with_empty_body_raises(self):
        with pytest.raises(ValueError, match="Message body is required"):
            TicketMessage.create(
                ticket_id="t1",
                author_id="u1",
                body="",
            )

    def test_create_strips_whitespace(self):
        msg = TicketMessage.create(
            ticket_id="t1",
            author_id="u1",
            body="  trimmed  ",
        )
        assert msg.body == "trimmed"
