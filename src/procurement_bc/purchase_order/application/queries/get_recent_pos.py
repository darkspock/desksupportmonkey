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


@dataclass
class GetRecentPurchaseOrdersQuery(Query):
    company_id: str
    limit: int = 5


class GetRecentPurchaseOrdersQueryHandler(
    QueryHandler[
        GetRecentPurchaseOrdersQuery,
        list[PurchaseOrder],
    ],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, query: GetRecentPurchaseOrdersQuery,
    ) -> list[PurchaseOrder]:
        pos, _ = self.po_repo.find_all(
            company_id=query.company_id,
            page=1,
            page_size=query.limit,
        )
        return pos
