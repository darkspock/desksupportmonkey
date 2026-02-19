from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.queries.get_recent_pos import (
    GetRecentPurchaseOrdersQuery,
    GetRecentPurchaseOrdersQueryHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
)


class TestGetRecentPurchaseOrdersQueryHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = GetRecentPurchaseOrdersQueryHandler(
            po_repo=self.po_repo,
        )

    def test_returns_recent_pos(self):
        pos = [
            PurchaseOrder.create(
                company_id="comp1",
                po_number="PO-2026-001",
                vendor_name="Vendor A",
                department_id="dept1",
                created_by="user1",
            ),
            PurchaseOrder.create(
                company_id="comp1",
                po_number="PO-2026-002",
                vendor_name="Vendor B",
                department_id="dept1",
                created_by="user1",
            ),
        ]
        self.po_repo.find_all.return_value = (pos, 2)

        result = self.handler.handle(
            GetRecentPurchaseOrdersQuery(company_id="comp1")
        )

        assert len(result) == 2
        assert result[0].po_number == "PO-2026-001"
        self.po_repo.find_all.assert_called_once_with(
            company_id="comp1",
            page=1,
            page_size=5,
        )

    def test_empty_list(self):
        self.po_repo.find_all.return_value = ([], 0)

        result = self.handler.handle(
            GetRecentPurchaseOrdersQuery(company_id="comp1")
        )

        assert result == []

    def test_custom_limit(self):
        self.po_repo.find_all.return_value = ([], 0)

        self.handler.handle(
            GetRecentPurchaseOrdersQuery(
                company_id="comp1", limit=10,
            )
        )

        self.po_repo.find_all.assert_called_once_with(
            company_id="comp1",
            page=1,
            page_size=10,
        )
