from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


@dataclass
class MyEquipmentQuery:
    user_id: str
    company_id: str


class MyEquipmentQueryHandler:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: MyEquipmentQuery) -> list[Asset]:
        return self.asset_repo.find_by_assigned_to(query.user_id, query.company_id)
