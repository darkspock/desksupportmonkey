from dataclasses import dataclass

from src.request_bc.request.domain.entities import RequestNote
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class ListNotesQuery:
    request_id: str
    company_id: str


class ListNotesQueryHandler:
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, query: ListNotesQuery) -> list[RequestNote]:
        request = self.request_repo.find_by_id(query.request_id, query.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{query.request_id}' not found")

        return self.request_repo.find_notes(query.request_id)
