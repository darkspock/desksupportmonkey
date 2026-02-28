from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.repository import RequestRepositoryInterface


@dataclass
class RequesterAssetDto:
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str]
    status: str
    is_affected: bool


@dataclass
class GetRequesterAssetsQuery(Query):
    request_id: str
    company_id: str


class GetRequesterAssetsQueryHandler(
    QueryHandler[GetRequesterAssetsQuery, list[RequesterAssetDto]],
):
    def __init__(
        self,
        request_repo: RequestRepositoryInterface,
        asset_repo: AssetRepositoryInterface,
    ):
        self.request_repo = request_repo
        self.asset_repo = asset_repo

    def handle(
        self, query: GetRequesterAssetsQuery,
    ) -> list[RequesterAssetDto]:
        request = self.request_repo.find_by_id(
            query.request_id, query.company_id,
        )
        if not request:
            return []

        requester_id = request.created_by
        assets = self.asset_repo.find_by_assigned_to(
            requester_id, query.company_id,
        )
        if not assets:
            return []

        affected_ids = set()
        if request.data:
            affected_ids = set(
                request.data.get("affected_asset_ids", [])
            )

        return [
            RequesterAssetDto(
                id=a.id,
                brand=a.brand,
                model=a.model,
                serial_number=a.serial_number,
                type=a.type,
                criticality=a.criticality.value if a.criticality else None,
                status=a.status.value,
                is_affected=a.id in affected_ids,
            )
            for a in assets
        ]
