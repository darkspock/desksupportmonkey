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
class MyShipmentsQuery(Query):
    recipient_user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20


class MyShipmentsQueryHandler(
    QueryHandler[
        MyShipmentsQuery,
        tuple[list[Shipment], int],
    ],
):
    def __init__(
        self,
        shipment_repo: ShipmentRepositoryInterface,
    ):
        self.shipment_repo = shipment_repo

    def handle(
        self, query: MyShipmentsQuery,
    ) -> tuple[list[Shipment], int]:
        return (
            self.shipment_repo
            .find_by_recipient_user_id(
                recipient_user_id=(
                    query.recipient_user_id
                ),
                company_id=query.company_id,
                page=query.page,
                page_size=query.page_size,
            )
        )
