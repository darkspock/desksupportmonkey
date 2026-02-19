import pytest

from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
)


def _make_item(
    po_id: str = "po1",
    quantity: int = 2,
    unit_cost_cents: int = 1000,
) -> PurchaseOrderItem:
    return PurchaseOrderItem(
        id="item1",
        purchase_order_id=po_id,
        description="Keyboard",
        quantity=quantity,
        unit_cost_cents=unit_cost_cents,
        total_cost_cents=quantity * unit_cost_cents,
    )


def _make_po(**kwargs) -> PurchaseOrder:
    defaults = dict(
        company_id="comp1",
        po_number="PO-2026-001",
        vendor_name="Acme Corp",
        department_id="dept1",
        currency="USD",
        created_by="user1",
    )
    defaults.update(kwargs)
    return PurchaseOrder.create(**defaults)


class TestPurchaseOrderCreate:
    def test_creates_with_draft_status(self):
        po = _make_po()
        assert po.status == PurchaseOrderStatus.DRAFT
        assert po.id is not None
        assert po.total_amount_cents == 0
        assert po.items == []
        assert po.request_ids == []

    def test_creates_with_ulid_id(self):
        po = _make_po()
        assert len(po.id) == 26


class TestPurchaseOrderSubmit:
    def test_submit_with_items(self):
        po = _make_po()
        item = _make_item(po_id=po.id)
        po.items.append(item)
        po.recalculate_total()
        po.submit()
        assert po.status == PurchaseOrderStatus.SUBMITTED

    def test_submit_without_items_raises(self):
        po = _make_po()
        with pytest.raises(ValueError, match="no items"):
            po.submit()

    def test_submit_with_zero_total_raises(self):
        po = _make_po()
        item = _make_item(
            po_id=po.id, unit_cost_cents=0,
        )
        po.items.append(item)
        with pytest.raises(ValueError, match="total <= 0"):
            po.submit()


class TestPurchaseOrderApprove:
    def test_approve_sets_approved_by(self):
        po = _make_po()
        po.items.append(_make_item(po_id=po.id))
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        assert po.status == PurchaseOrderStatus.APPROVED
        assert po.approved_by == "admin1"
        assert po.approved_at is not None


class TestPurchaseOrderReject:
    def test_reject_sets_cancellation_reason(self):
        po = _make_po()
        po.items.append(_make_item(po_id=po.id))
        po.recalculate_total()
        po.submit()
        po.reject("Too expensive")
        assert po.status == PurchaseOrderStatus.CANCELLED
        assert po.cancellation_reason == "Too expensive"


class TestPurchaseOrderMarkOrdered:
    def test_mark_ordered_from_approved(self):
        po = _make_po()
        po.items.append(_make_item(po_id=po.id))
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        po.mark_ordered()
        assert po.status == PurchaseOrderStatus.ORDERED
        assert po.ordered_at is not None


class TestPurchaseOrderCancel:
    def test_cancel_from_draft(self):
        po = _make_po()
        po.cancel("No longer needed")
        assert po.status == PurchaseOrderStatus.CANCELLED
        assert po.cancellation_reason == "No longer needed"

    def test_cancel_from_ordered(self):
        po = _make_po()
        po.items.append(_make_item(po_id=po.id))
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        po.mark_ordered()
        po.cancel("Vendor issue")
        assert po.status == PurchaseOrderStatus.CANCELLED


class TestPurchaseOrderReceive:
    def test_receive_all_transitions_to_received(self):
        po = _make_po()
        item = _make_item(po_id=po.id, quantity=2)
        po.items.append(item)
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        po.mark_ordered()
        item.received_quantity = 2
        po.receive()
        assert po.status == PurchaseOrderStatus.RECEIVED

    def test_receive_partial_transitions_to_partially_received(
        self,
    ):
        po = _make_po()
        item = _make_item(po_id=po.id, quantity=5)
        po.items.append(item)
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        po.mark_ordered()
        item.received_quantity = 2
        po.receive()
        assert (
            po.status
            == PurchaseOrderStatus.PARTIALLY_RECEIVED
        )


class TestPurchaseOrderClose:
    def test_close_from_received(self):
        po = _make_po()
        item = _make_item(po_id=po.id)
        po.items.append(item)
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        po.mark_ordered()
        item.received_quantity = item.quantity
        po.receive()
        po.close()
        assert po.status == PurchaseOrderStatus.CLOSED


class TestPurchaseOrderInvalidTransitions:
    def test_cannot_approve_from_draft(self):
        po = _make_po()
        with pytest.raises(InvalidPOStatusTransitionError):
            po.approve("admin1")

    def test_cannot_order_from_draft(self):
        po = _make_po()
        with pytest.raises(InvalidPOStatusTransitionError):
            po.mark_ordered()

    def test_cannot_submit_from_approved(self):
        po = _make_po()
        po.items.append(_make_item(po_id=po.id))
        po.recalculate_total()
        po.submit()
        po.approve("admin1")
        with pytest.raises(InvalidPOStatusTransitionError):
            po.submit()


class TestRecalculateTotal:
    def test_recalculate_total(self):
        po = _make_po()
        po.items.append(
            _make_item(
                po_id=po.id,
                quantity=2,
                unit_cost_cents=1000,
            )
        )
        po.items.append(
            PurchaseOrderItem(
                id="item2",
                purchase_order_id=po.id,
                description="Mouse",
                quantity=3,
                unit_cost_cents=500,
                total_cost_cents=1500,
            )
        )
        po.recalculate_total()
        assert po.total_amount_cents == 3500
