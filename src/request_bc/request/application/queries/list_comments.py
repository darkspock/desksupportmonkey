from dataclasses import dataclass

from src.request_bc.request.domain.entities import RequestComment
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class ListCommentsQuery:
    request_id: str
    company_id: str


class ListCommentsQueryHandler:
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, query: ListCommentsQuery) -> list[RequestComment]:
        request = self.request_repo.find_by_id(query.request_id, query.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{query.request_id}' not found")

        return self.request_repo.find_comments(query.request_id)
