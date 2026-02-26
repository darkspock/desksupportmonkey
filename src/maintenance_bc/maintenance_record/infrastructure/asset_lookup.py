from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
    AssetStatusUpdater,
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


class AssetStatusUpdaterAdapter(AssetStatusUpdater):
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def set_status_in_stock(
        self,
        asset_id: str,
        company_id: str,
        performed_by: str,
    ) -> None:
        asset = self.asset_repo.find_by_id(asset_id, company_id)
        if not asset:
            return
        asset.change_status(AssetStatus.IN_STOCK)
        self.asset_repo.save(asset)
        self.asset_repo.save_event(
            AssetEvent.create(
                asset_id=asset_id,
                event_type="maintenance_completed_auto_stock",
                data={"previous_status": "in_repair"},
                performed_by=performed_by,
            )
        )
