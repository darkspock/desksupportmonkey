from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.repository import RequestRepositoryInterface


@dataclass
class ListRequestsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    subtype: Optional[str] = None


class ListRequestsQueryHandler(QueryHandler[ListRequestsQuery, tuple[list[ServiceRequest], int]]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, query: ListRequestsQuery) -> tuple[list[ServiceRequest], int]:
        return self.request_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            search=query.search,
            status=query.status,
            type=query.type,
            priority=query.priority,
            assigned_to=query.assigned_to,
            subtype=query.subtype,
        )
