from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


class AssetNotFoundError(Exception):
    pass


@dataclass
class GetAssetQuery:
    asset_id: str
    company_id: str


class GetAssetQueryHandler:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: GetAssetQuery) -> Asset:
        asset = self.asset_repo.find_by_id(query.asset_id, query.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset '{query.asset_id}' not found")
        return asset
