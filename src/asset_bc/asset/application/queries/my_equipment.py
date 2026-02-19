from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class MyEquipmentQuery(Query):
    user_id: str
    company_id: str


class MyEquipmentQueryHandler(QueryHandler[MyEquipmentQuery, list[Asset]]):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: MyEquipmentQuery) -> list[Asset]:
        return self.asset_repo.find_by_assigned_to(query.user_id, query.company_id)
