import logging
from datetime import date

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetType
from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
)
from src.procurement_bc.purchase_order.domain.entities import (
    PurchaseOrderItem,
)

logger = logging.getLogger(__name__)


class ReceiptAssetService:
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
    ):
        self.asset_repo = asset_repo

    def create_asset_from_item(
        self,
        company_id: str,
        po_item: PurchaseOrderItem,
        vendor_name: str,
        received_by: str,
    ) -> str:
        asset_type = AssetType(po_item.asset_type)
        asset = Asset.create(
            company_id=company_id,
            type=asset_type,
            brand=vendor_name,
            model=po_item.description,
            serial_number=f"PO-{po_item.purchase_order_id[:8]}-{po_item.id[:8]}",
            purchase_date=date.today(),
            notes=f"Created from PO item: {po_item.description}",
        )
        asset.purchase_cost_cents = po_item.unit_cost_cents
        saved = self.asset_repo.save(asset)
        logger.info(
            "Created asset %s from PO item %s",
            saved.id,
            po_item.id,
        )
        return saved.id
