import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.close_po import (
    ClosePurchaseOrderCommand,
    ClosePurchaseOrderCommandHandler,
    InvalidCloseStatusError,
    PONotFoundError,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)


def _make_received_po() -> PurchaseOrder:
    po = PurchaseOrder.create(
        company_id="comp1",
        po_number="PO-2026-001",
        vendor_name="Vendor",
        department_id="dept1",
        created_by="user1",
    )
    po.items = [
        PurchaseOrderItem(
            id="item1",
            purchase_order_id=po.id,
            description="Laptop",
            quantity=2,
            unit_cost_cents=50000,
            total_cost_cents=100000,
            received_quantity=2,
        ),
    ]
    po.recalculate_total()
    po.submit()
    po.approve(approved_by="admin1")
    po.mark_ordered()
    po.receive()  # All received → RECEIVED
    return po


def _make_partially_received_po() -> PurchaseOrder:
    po = PurchaseOrder.create(
        company_id="comp1",
        po_number="PO-2026-002",
        vendor_name="Vendor",
        department_id="dept1",
        created_by="user1",
    )
    po.items = [
        PurchaseOrderItem(
            id="item1",
            purchase_order_id=po.id,
            description="Laptop",
            quantity=3,
            unit_cost_cents=50000,
            total_cost_cents=150000,
            received_quantity=1,
        ),
    ]
    po.recalculate_total()
    po.submit()
    po.approve(approved_by="admin1")
    po.mark_ordered()
    po.receive()  # Not all → PARTIALLY_RECEIVED
    return po


class TestClosePurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = ClosePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
        )

    def test_close_from_received(self):
        po = _make_received_po()
        assert po.status == PurchaseOrderStatus.RECEIVED
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ClosePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                performed_by="tech1",
            )
        )

        assert po.status == PurchaseOrderStatus.CLOSED
        self.po_repo.save.assert_called_once()

    def test_close_from_partially_received(self):
        po = _make_partially_received_po()
        assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ClosePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                performed_by="tech1",
            )
        )

        assert po.status == PurchaseOrderStatus.CLOSED

    def test_close_from_invalid_status_raises(self):
        po = PurchaseOrder.create(
            company_id="comp1",
            po_number="PO-001",
            vendor_name="V",
            department_id="d1",
            created_by="u1",
        )
        po.items = [
            PurchaseOrderItem(
                id="i1",
                purchase_order_id=po.id,
                description="Item",
                quantity=1,
                unit_cost_cents=1000,
                total_cost_cents=1000,
            ),
        ]
        po.recalculate_total()
        po.submit()
        po.approve(approved_by="admin1")
        po.mark_ordered()
        assert po.status == PurchaseOrderStatus.ORDERED
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(InvalidCloseStatusError):
            self.handler.handle(
                ClosePurchaseOrderCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    performed_by="tech1",
                )
            )

    def test_po_not_found_raises(self):
        self.po_repo.find_by_id.return_value = None

        with pytest.raises(PONotFoundError):
            self.handler.handle(
                ClosePurchaseOrderCommand(
                    purchase_order_id="nope",
                    company_id="comp1",
                    performed_by="tech1",
                )
            )
