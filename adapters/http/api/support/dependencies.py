from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.support_bc.ticket.infrastructure.repository import SupportTicketRepository


def get_ticket_repo(
    db: Session = Depends(get_db),
) -> SupportTicketRepository:
    return SupportTicketRepository(db)
