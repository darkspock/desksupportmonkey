import logging

from core.celery import celery_app
from core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="core.tasks.support_tickets.auto_close_stale_tickets")
def auto_close_stale_tickets():
    """Auto-close resolved tickets (>7 days) and stale active tickets (>30 days)."""
    from src.support_bc.ticket.domain.enums import TicketStatus
    from src.support_bc.ticket.infrastructure.repository import (
        SupportTicketRepository,
    )

    session = SessionLocal()
    try:
        repo = SupportTicketRepository(session)
        closed_count = 0

        # 1. Close resolved tickets older than 7 days
        resolved_tickets = repo.find_resolved_older_than_days(7)
        for ticket in resolved_tickets:
            ticket.change_status(TicketStatus.CLOSED)
            repo.save(ticket)
            closed_count += 1

        # 2. Close stale active tickets older than 30 days
        stale_tickets = repo.find_stale_older_than_days(30)
        for ticket in stale_tickets:
            ticket.change_status(TicketStatus.CLOSED)
            repo.save(ticket)
            closed_count += 1

        session.commit()
        logger.info("Auto-closed %d support tickets", closed_count)
        return closed_count
    except Exception:
        session.rollback()
        logger.exception("Failed to auto-close stale tickets")
        raise
    finally:
        session.close()
