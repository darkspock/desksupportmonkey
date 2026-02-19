from unittest.mock import MagicMock

from src.procurement_bc.purchase_order.application.services.receipt_asset_service import (
    ReceiptAssetService,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrderItem,
)


class TestReceiptAssetService:
    def setup_method(self):
        self.asset_repo = MagicMock()
        self.service = ReceiptAssetService(
            asset_repo=self.asset_repo,
        )

    def test_create_asset_from_item(self):
        self.asset_repo.save.side_effect = lambda a: a

        po_item = PurchaseOrderItem(
            id="item1",
            purchase_order_id="po1",
            description="Dell Latitude 5550",
            quantity=2,
            unit_cost_cents=80000,
            total_cost_cents=160000,
            asset_type="laptop",
        )

        asset_id = self.service.create_asset_from_item(
            company_id="comp1",
            po_item=po_item,
            vendor_name="Dell Inc",
            received_by="tech1",
        )

        assert asset_id is not None
        self.asset_repo.save.assert_called_once()
        saved_asset = self.asset_repo.save.call_args[0][0]
        assert saved_asset.company_id == "comp1"
        assert saved_asset.type.value == "laptop"
        assert saved_asset.brand == "Dell Inc"
        assert saved_asset.model == "Dell Latitude 5550"
        assert saved_asset.purchase_cost_cents == 80000
