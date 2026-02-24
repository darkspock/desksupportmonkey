from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
    AssetSummary,
)


class AssetRepositoryLookupAdapter(AssetLookup):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
    ):
        self.asset_repo = asset_repo

    def exists(
        self,
        asset_id: str,
        company_id: str,
    ) -> bool:
        return self.asset_repo.find_by_id(asset_id, company_id) is not None

    def list_by_company(
        self,
        company_id: str,
    ) -> list[AssetSummary]:
        assets = self.asset_repo.find_all_by_company(company_id)
        return [
            AssetSummary(id=asset.id, type=asset.type)
            for asset in assets
        ]
