from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.support_bc.ticket.domain.entities import SupportTicket, TicketMessage
from src.support_bc.ticket.domain.exceptions import TicketNotFoundError
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class TicketDetail:
    ticket: SupportTicket
    messages: list[TicketMessage]


@dataclass
class GetTicketDetailQuery(Query):
    ticket_id: str
    company_id: Optional[str] = None  # None for super admin


class GetTicketDetailQueryHandler(
    QueryHandler[GetTicketDetailQuery, TicketDetail]
):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, query: GetTicketDetailQuery) -> TicketDetail:
        if query.company_id:
            ticket = self.ticket_repo.find_by_id(
                query.ticket_id, query.company_id
            )
        else:
            ticket = self.ticket_repo.find_by_id_any_company(query.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        messages = self.ticket_repo.find_messages(query.ticket_id)
        return TicketDetail(ticket=ticket, messages=messages)
