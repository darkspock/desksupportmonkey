from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.reseller.application.dtos import ResellerDto, ResellerListDto
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class ListResellersQuery(Query):
    offset: int = 0
    limit: int = 50


class ListResellersQueryHandler(QueryHandler[ListResellersQuery, ResellerListDto]):
    def __init__(self, repo: ResellerRepositoryInterface):
        self.repo = repo

    def handle(self, query: ListResellersQuery) -> ResellerListDto:
        resellers = self.repo.list_all(query.offset, query.limit)
        total = self.repo.count_all()
        return ResellerListDto(
            items=[ResellerDto.from_entity(r) for r in resellers],
            total=total,
        )
