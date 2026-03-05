from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.support_bc.ticket.domain.entities import SupportTicket
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class ListAllTicketsQuery(Query):
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    search: Optional[str] = None
    company_id: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class ListAllTicketsQueryHandler(
    QueryHandler[ListAllTicketsQuery, tuple[list[SupportTicket], int]]
):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(
        self, query: ListAllTicketsQuery
    ) -> tuple[list[SupportTicket], int]:
        return self.ticket_repo.find_all(
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            category=query.category,
            priority=query.priority,
            search=query.search,
            company_id=query.company_id,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
