from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.support_bc.ticket.domain.repository import SupportTicketRepositoryInterface


@dataclass
class GetTicketStatsQuery(Query):
    pass


class GetTicketStatsQueryHandler(
    QueryHandler[GetTicketStatsQuery, dict[str, int]]
):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, query: GetTicketStatsQuery) -> dict[str, int]:
        return self.ticket_repo.count_by_status()
