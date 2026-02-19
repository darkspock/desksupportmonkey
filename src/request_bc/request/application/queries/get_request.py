from dataclasses import dataclass
from typing import NamedTuple

from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


class RequestDetail(NamedTuple):
    request: ServiceRequest
    comment_count: int


@dataclass
class GetRequestQuery(Query):
    request_id: str
    company_id: str


class GetRequestQueryHandler(QueryHandler[GetRequestQuery, RequestDetail]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, query: GetRequestQuery) -> RequestDetail:
        request = self.request_repo.find_by_id(query.request_id, query.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{query.request_id}' not found")

        comment_count = self.request_repo.count_comments(request.id)

        return RequestDetail(request=request, comment_count=comment_count)
