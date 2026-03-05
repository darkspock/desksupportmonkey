from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


def _make_ticket(ticket_id, status, resolved_at=None):
    return SupportTicket(
        id=ticket_id,
        reference=f"SUP-{ticket_id}",
        company_id="c1",
        created_by="u1",
        category=TicketCategory.BUG_REPORT,
        subject="Test",
        description="Test desc",
        status=status,
        priority=TicketPriority.MEDIUM,
        resolved_at=resolved_at,
    )


class TestAutoCloseStaleTickets:
    @patch("core.tasks.support_tickets.SessionLocal")
    @patch(
        "src.support_bc.ticket.infrastructure.repository.SupportTicketRepository"
    )
    def test_closes_resolved_and_stale_tickets(self, mock_repo_cls, mock_session_cls):
        from core.tasks.support_tickets import auto_close_stale_tickets

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        resolved_ticket = _make_ticket(
            "t1",
            TicketStatus.RESOLVED,
            resolved_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        stale_ticket = _make_ticket("t2", TicketStatus.OPEN)

        mock_repo.find_resolved_older_than_days.return_value = [resolved_ticket]
        mock_repo.find_stale_older_than_days.return_value = [stale_ticket]
        mock_repo.save.side_effect = lambda t: t

        result = auto_close_stale_tickets()

        assert result == 2
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        assert mock_repo.save.call_count == 2

    @patch("core.tasks.support_tickets.SessionLocal")
    @patch(
        "src.support_bc.ticket.infrastructure.repository.SupportTicketRepository"
    )
    def test_rollback_on_exception(self, mock_repo_cls, mock_session_cls):
        from core.tasks.support_tickets import auto_close_stale_tickets

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        mock_repo.find_resolved_older_than_days.side_effect = Exception("DB error")

        try:
            auto_close_stale_tickets()
        except Exception:
            pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("core.tasks.support_tickets.SessionLocal")
    @patch(
        "src.support_bc.ticket.infrastructure.repository.SupportTicketRepository"
    )
    def test_no_tickets_to_close(self, mock_repo_cls, mock_session_cls):
        from core.tasks.support_tickets import auto_close_stale_tickets

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        mock_repo.find_resolved_older_than_days.return_value = []
        mock_repo.find_stale_older_than_days.return_value = []

        result = auto_close_stale_tickets()

        assert result == 0
        mock_session.commit.assert_called_once()
