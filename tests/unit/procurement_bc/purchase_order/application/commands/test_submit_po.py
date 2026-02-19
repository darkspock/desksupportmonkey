import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.submit_po import (
    PONotFoundError,
    SubmitPurchaseOrderCommand,
    SubmitPurchaseOrderCommandHandler,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)


def _make_draft_po(
    total_cents: int = 10000,
) -> PurchaseOrder:
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
            unit_cost_cents=total_cents,
            total_cost_cents=total_cents,
        )
    )
    po.recalculate_total()
    return po


class TestSubmitPurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.config_repo = MagicMock()
        self.handler = SubmitPurchaseOrderCommandHandler(
            po_repo=self.po_repo,
            config_repo=self.config_repo,
        )

    def _cmd(self, **overrides):
        defaults = dict(
            purchase_order_id="po1",
            company_id="comp1",
            performed_by="user1",
        )
        defaults.update(overrides)
        return SubmitPurchaseOrderCommand(**defaults)

    def test_submit_valid_po(self):
        po = _make_draft_po()
        self.po_repo.find_by_id.return_value = po
        self.config_repo.find_by_company_id.return_value = (
            None
        )

        self.handler.handle(self._cmd())
        result = self.handler.last_result

        assert result.auto_approved is False
        assert po.status == PurchaseOrderStatus.SUBMITTED
        self.po_repo.save.assert_called_once()

    def test_submit_not_found_raises(self):
        self.po_repo.find_by_id.return_value = None
        with pytest.raises(PONotFoundError):
            self.handler.handle(self._cmd())

    def test_submit_auto_approval_below_threshold(self):
        po = _make_draft_po(total_cents=5000)
        self.po_repo.find_by_id.return_value = po
        config = CompanyProcurementConfig.defaults("comp1")
        config.approval_threshold_cents = 10000
        self.config_repo.find_by_company_id.return_value = (
            config
        )

        self.handler.handle(self._cmd())
        result = self.handler.last_result

        assert result.auto_approved is True
        assert po.status == PurchaseOrderStatus.APPROVED

    def test_submit_no_auto_approval_above_threshold(self):
        po = _make_draft_po(total_cents=50000)
        self.po_repo.find_by_id.return_value = po
        config = CompanyProcurementConfig.defaults("comp1")
        config.approval_threshold_cents = 10000
        self.config_repo.find_by_company_id.return_value = (
            config
        )

        self.handler.handle(self._cmd())
        result = self.handler.last_result

        assert result.auto_approved is False
        assert po.status == PurchaseOrderStatus.SUBMITTED
