import pytest
from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.commands.create_po import (
    CreatePurchaseOrderCommand,
    CreatePurchaseOrderCommandHandler,
    POItemInput,
)
from src.procurement_bc.budget.domain.entities import (
    CompanyProcurementConfig,
)


class TestCreatePurchaseOrderCommandHandler:
    def setup_method(self):
        self.po_repo = MagicMock()
        self.config_repo = MagicMock()
        self.handler = CreatePurchaseOrderCommandHandler(
            po_repo=self.po_repo,
            config_repo=self.config_repo,
        )
        self.po_repo.get_next_number.return_value = 1

    def _cmd(self, **overrides):
        defaults = dict(
            company_id="comp1",
            vendor_name="Acme Corp",
            department_id="dept1",
            items=[
                POItemInput(
                    description="Laptop",
                    quantity=2,
                    unit_cost_cents=50000,
                ),
            ],
            request_ids=[],
            performed_by="user1",
        )
        defaults.update(overrides)
        return CreatePurchaseOrderCommand(**defaults)

    def test_create_with_items(self):
        config = CompanyProcurementConfig.defaults("comp1")
        self.config_repo.find_by_company_id.return_value = (
            config
        )

        self.handler.handle(self._cmd())

        assert isinstance(self.handler.last_created_id, str)
        self.po_repo.save.assert_called_once()
        saved = self.po_repo.save.call_args[0][0]
        assert len(saved.items) == 1
        assert saved.items[0].total_cost_cents == 100000
        assert saved.total_amount_cents == 100000
        assert saved.vendor_name == "Acme Corp"

    def test_create_generates_po_number(self):
        config = CompanyProcurementConfig.defaults("comp1")
        self.config_repo.find_by_company_id.return_value = (
            config
        )

        self.handler.handle(self._cmd())

        saved = self.po_repo.save.call_args[0][0]
        assert saved.po_number.startswith("PO-")
        assert "-001" in saved.po_number

    def test_create_no_items_raises(self):
        self.config_repo.find_by_company_id.return_value = (
            None
        )
        with pytest.raises(ValueError, match="item"):
            self.handler.handle(self._cmd(items=[]))

    def test_create_uses_default_config(self):
        self.config_repo.find_by_company_id.return_value = (
            None
        )

        self.handler.handle(self._cmd())

        saved = self.po_repo.save.call_args[0][0]
        assert saved.currency == "USD"
