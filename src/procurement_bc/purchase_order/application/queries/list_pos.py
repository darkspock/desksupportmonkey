from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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
class ListPurchaseOrdersQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    vendor_id: Optional[str] = None
    department_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ListPurchaseOrdersQueryHandler(
    QueryHandler[
        ListPurchaseOrdersQuery,
        tuple[list[PurchaseOrder], int],
    ],
):
    def __init__(
        self,
        po_repo: PurchaseOrderRepositoryInterface,
    ):
        self.po_repo = po_repo

    def handle(
        self, query: ListPurchaseOrdersQuery,
    ) -> tuple[list[PurchaseOrder], int]:
        return self.po_repo.find_all(
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
            vendor_id=query.vendor_id,
            department_id=query.department_id,
            date_from=query.date_from,
            date_to=query.date_to,
        )
