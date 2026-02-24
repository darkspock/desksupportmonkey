from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import AssetLocation
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListLocationsQuery(Query):
    company_id: str


class ListLocationsQueryHandler(QueryHandler[ListLocationsQuery, list[AssetLocation]]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: ListLocationsQuery) -> list[AssetLocation]:
        return self.asset_repo.find_locations_by_company(query.company_id)
