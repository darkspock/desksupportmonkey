from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.repository import AssetRepositoryInterface


@dataclass
class ListAssetsQuery:
    company_id: str
    page: int = 1
    page_size: int = 20


class ListAssetsQueryHandler:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def handle(self, query: ListAssetsQuery) -> tuple[list[Asset], int]:
        return self.asset_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
        )
