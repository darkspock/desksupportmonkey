import pytest
from unittest.mock import MagicMock

from src.procurement_bc.budget.application.services.budget_checker import (
    BudgetCheckResult,
)
from src.procurement_bc.purchase_order.application.commands.approve_po import (
    ApprovePurchaseOrderCommand,
    ApprovePurchaseOrderCommandHandler,
    BudgetExceededException,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from src.procurement_bc.purchase_order.domain.enums import (
    PurchaseOrderStatus,
)


def _make_submitted_po(
    total: int = 10000,
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
            unit_cost_cents=total,
            total_cost_cents=total,
        )
    )
    po.recalculate_total()
    po.submit()
    return po


class TestApproveWithBudget:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.budget_checker = MagicMock()

    def test_strict_enforcement_blocks_approval(self):
        po = _make_submitted_po(50000)
        self.po_repo.find_by_id.return_value = po
        self.budget_checker.check_approval.return_value = (
            BudgetCheckResult(
                allowed=False,
                warning="Budget exceeded by $100.00",
                remaining_cents=-10000,
                spent_cents=60000,
                allocated_cents=100000,
            )
        )

        handler = ApprovePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
            budget_checker=self.budget_checker,
        )

        with pytest.raises(BudgetExceededException):
            handler.handle(
                ApprovePurchaseOrderCommand(
                    purchase_order_id=po.id,
                    company_id="comp1",
                    approved_by="admin1",
                )
            )
        assert po.status == PurchaseOrderStatus.SUBMITTED

    def test_warn_enforcement_allows_with_warning(self):
        po = _make_submitted_po(50000)
        self.po_repo.find_by_id.return_value = po
        self.budget_checker.check_approval.return_value = (
            BudgetCheckResult(
                allowed=True,
                warning="Over budget by $100.00",
                remaining_cents=-10000,
                spent_cents=60000,
                allocated_cents=100000,
            )
        )
        self.budget_checker.check_threshold.return_value = False

        handler = ApprovePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
            budget_checker=self.budget_checker,
        )

        handler.handle(
            ApprovePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                approved_by="admin1",
            )
        )
        result = handler.last_result

        assert po.status == PurchaseOrderStatus.APPROVED
        assert result.budget_warning is not None
        self.po_repo.save.assert_called_once()

    def test_approve_without_budget_checker(self):
        po = _make_submitted_po()
        self.po_repo.find_by_id.return_value = po

        handler = ApprovePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
        )

        handler.handle(
            ApprovePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                approved_by="admin1",
            )
        )
        result = handler.last_result

        assert po.status == PurchaseOrderStatus.APPROVED
        assert result.budget_warning is None

    def test_threshold_crossed_sets_flag(self):
        po = _make_submitted_po(20000)
        self.po_repo.find_by_id.return_value = po
        self.budget_checker.check_approval.return_value = (
            BudgetCheckResult(
                allowed=True,
                warning=None,
                remaining_cents=0,
                spent_cents=60000,
                allocated_cents=100000,
            )
        )
        self.budget_checker.check_threshold.return_value = True

        handler = ApprovePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
            budget_checker=self.budget_checker,
        )

        handler.handle(
            ApprovePurchaseOrderCommand(
                purchase_order_id=po.id,
                company_id="comp1",
                approved_by="admin1",
            )
        )
        result = handler.last_result

        assert result.threshold_crossed is True
        assert result.spent_cents == 80000
