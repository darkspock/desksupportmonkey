from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.reject_po import (
    RejectPurchaseOrderCommand,
    RejectPurchaseOrderCommandHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)


def _make_submitted_po() -> PurchaseOrder:
    po = PurchaseOrder.create(
        company_id="comp1",
        po_number="PO-2026-001",
        vendor_name="Vendor",
        department_id="dept1",
        created_by="user1",
    )
    po.items.append(
        PurchaseOrderItem(
            id="item1",
            purchase_order_id=po.id,
            description="Item",
            quantity=1,
            unit_cost_cents=10000,
            total_cost_cents=10000,
        )
    )
    po.recalculate_total()
    po.submit()
    return po


class TestRejectPurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = RejectPurchaseOrderCommandHandler(
            po_repo=self.po_repo,
        )

    def test_reject_with_reason(self):
        po = _make_submitted_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            RejectPurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                reason="Over budget",
                performed_by="admin1",
            )
        )

        assert po.status == PurchaseOrderStatus.CANCELLED
        assert po.cancellation_reason == "Over budget"
        self.po_repo.save.assert_called_once()
