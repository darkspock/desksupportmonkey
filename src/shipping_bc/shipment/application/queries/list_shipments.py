from dataclasses import dataclass
from typing import Optional

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
class ListShipmentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    direction: Optional[str] = None
    destination_type: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None


class ListShipmentsQueryHandler(
    QueryHandler[
        ListShipmentsQuery,
        tuple[list[Shipment], int],
    ],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, query: ListShipmentsQuery,
    ) -> tuple[list[Shipment], int]:
        return self.shipment_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            direction=query.direction,
            destination_type=query.destination_type,
            request_id=query.request_id,
            po_id=query.po_id,
        )
