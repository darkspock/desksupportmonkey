import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.approve_po import (
    ApprovePurchaseOrderCommand,
    ApprovePurchaseOrderCommandHandler,
    PONotFoundError,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    InvalidPOStatusTransitionError,
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


class TestApprovePurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.handler = ApprovePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
        )

    def test_approve_submitted_po(self):
        po = _make_submitted_po()
        self.po_repo.find_by_id.return_value = po

        self.handler.handle(
            ApprovePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                approved_by="admin1",
            )
        )
        result = self.handler.last_result

        assert po.status == PurchaseOrderStatus.APPROVED
        assert po.approved_by == "admin1"
        assert result.budget_warning is None
        self.po_repo.save.assert_called_once()

    def test_approve_non_submitted_raises(self):
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
                ApprovePurchaseOrderCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    approved_by="admin1",
                )
            )
