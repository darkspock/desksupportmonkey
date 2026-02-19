import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.cancel_po import (
    CancelPurchaseOrderCommand,
    CancelPurchaseOrderCommandHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
)


def _make_po(status: PurchaseOrderStatus) -> PurchaseOrder:
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
    # Force status for testing
    po.status = status
    return po


class TestCancelPurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = CancelPurchaseOrderCommandHandler(
            po_repo=self.po_repo,
        )

    def _cmd(self, po_id: str = "po1"):
        return CancelPurchaseOrderCommand(
            purchase_order_id=po_id,
            company_id="comp1",
            reason="No longer needed",
            performed_by="user1",
        )

    @pytest.mark.parametrize(
        "status",
        [
            PurchaseOrderStatus.DRAFT,
            PurchaseOrderStatus.SUBMITTED,
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.ORDERED,
        ],
    )
    def test_cancel_from_valid_state(self, status):
        po = _make_po(status)
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(self._cmd(po.id))

        assert po.status == PurchaseOrderStatus.CANCELLED
        assert po.cancellation_reason == "No longer needed"

    def test_cancel_from_received_raises(self):
        po = _make_po(PurchaseOrderStatus.RECEIVED)
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(InvalidPOStatusTransitionError):
            self.handler.handle(self._cmd(po.id))
