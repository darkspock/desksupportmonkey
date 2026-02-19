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


class ShipmentNotFoundError(Exception):
    pass


@dataclass
class GetShipmentQuery(Query):
    shipment_id: str
    company_id: str


class GetShipmentQueryHandler(
    QueryHandler[GetShipmentQuery, Shipment],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, query: GetShipmentQuery,
    ) -> Shipment:
        shipment = self.shipment_repo.find_by_id(
            query.shipment_id, query.company_id,
        )
        if not shipment:
            raise ShipmentNotFoundError(
                f"Shipment {query.shipment_id} "
                f"not found",
            )
        return shipment
