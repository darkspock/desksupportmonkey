from dataclasses import dataclass

from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
)
from src.procurement_bc.purchase_order.domain.repository import (
    PurchaseOrderRepositoryInterface,
)
from src.framework.application.query_bus import (
    Query,
    QueryHandler,
)


class PONotFoundError(Exception):
    pass


@dataclass
class GetPurchaseOrderQuery(Query):
    purchase_order_id: str
    company_id: str


class GetPurchaseOrderQueryHandler(
    QueryHandler[
        GetPurchaseOrderQuery,
        PurchaseOrder,
    ],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, query: GetPurchaseOrderQuery,
    ) -> PurchaseOrder:
        po = self.po_repo.find_by_id(
            query.purchase_order_id,
            query.company_id,
        )
        if not po:
            raise PONotFoundError(
                f"PO {query.purchase_order_id} not found"
            )
        return po
