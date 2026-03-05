from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.reseller.application.dtos import ResellerDto
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class GetResellerByIdQuery(Query):
    reseller_id: str


class GetResellerByIdQueryHandler(QueryHandler[GetResellerByIdQuery, Optional[ResellerDto]]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetResellerByIdQuery) -> Optional[ResellerDto]:
        reseller = self.repo.get_by_id(query.reseller_id)
        if reseller is None:
            return None
        return ResellerDto.from_entity(reseller)
