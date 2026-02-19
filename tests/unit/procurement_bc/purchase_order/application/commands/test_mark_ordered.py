import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.mark_ordered import (  # noqa: E501
    MarkOrderedCommand,
    MarkOrderedCommandHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
    PurchaseOrderStatus,
)


def _make_approved_po() -> PurchaseOrder:
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
    po.approve("admin1")
    return po


class TestMarkOrderedCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = MarkOrderedCommandHandler(
            po_repo=self.po_repo,
        )

    def test_mark_ordered_from_approved(self):
        po = _make_approved_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            MarkOrderedCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                performed_by="user1",
            )
        )

        assert po.status == PurchaseOrderStatus.ORDERED
        assert po.ordered_at is not None
        self.po_repo.save.assert_called_once()

    def test_mark_ordered_from_draft_raises(self):
        po = PurchaseOrder.create(
            company_id="comp1",
            po_number="PO-2026-001",
            vendor_name="Vendor",
            department_id="dept1",
            created_by="user1",
        )
        self.po_repo.find_by_id.return_value = po

        with pytest.raises(InvalidPOStatusTransitionError):
            self.handler.handle(
                MarkOrderedCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    performed_by="user1",
                )
            )
