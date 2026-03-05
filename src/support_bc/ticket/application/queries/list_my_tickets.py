from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class ListMyTicketsQuery(Query):
    user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None


class ListMyTicketsQueryHandler(
    QueryHandler[ListMyTicketsQuery, tuple[list[SupportTicket], int]]
):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(
        self, query: ListMyTicketsQuery
    ) -> tuple[list[SupportTicket], int]:
        return self.ticket_repo.find_by_created_by(
            user_id=query.user_id,
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
        )
