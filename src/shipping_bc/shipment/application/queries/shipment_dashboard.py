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
class ShipmentDashboardResult:
    active_by_status: dict[str, int]
    recent_deliveries: list[Shipment]
    failed_count: int


@dataclass
class ShipmentDashboardQuery(Query):
    company_id: str


class ShipmentDashboardQueryHandler(
    QueryHandler[
        ShipmentDashboardQuery,
        ShipmentDashboardResult,
    ],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, query: ShipmentDashboardQuery,
    ) -> ShipmentDashboardResult:
        counts = self.shipment_repo.count_by_status(
            query.company_id,
        )
        recent = (
            self.shipment_repo.find_recent_delivered(
                query.company_id, days=7,
            )
        )
        failed = self.shipment_repo.find_by_status(
            query.company_id, "FAILED",
        )

        return ShipmentDashboardResult(
            active_by_status=counts,
            recent_deliveries=recent,
            failed_count=len(failed),
        )
