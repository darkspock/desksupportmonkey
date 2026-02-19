from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.repository import RequestRepositoryInterface


@dataclass
class MyRequestsQuery(Query):
    user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    subtype: Optional[str] = None


class MyRequestsQueryHandler(QueryHandler[MyRequestsQuery, tuple[list[ServiceRequest], int]]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, query: MyRequestsQuery) -> tuple[list[ServiceRequest], int]:
        return self.request_repo.find_by_created_by(
            user_id=query.user_id,
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            subtype=query.subtype,
        )
