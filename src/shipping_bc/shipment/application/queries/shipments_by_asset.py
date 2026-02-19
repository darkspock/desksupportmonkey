from dataclasses import dataclass

from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
)
from src.shipping_bc.shipment.domain.repository import (
    ShipmentRepositoryInterface,
)


@dataclass
class ShipmentsByAssetQuery(Query):
    asset_id: str
    company_id: str


class ShipmentsByAssetQueryHandler(
    QueryHandler[
        ShipmentsByAssetQuery, list[Shipment],
    ],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, query: ShipmentsByAssetQuery,
    ) -> list[Shipment]:
        return self.shipment_repo.find_by_asset_id(
            query.asset_id, query.company_id,
        )
