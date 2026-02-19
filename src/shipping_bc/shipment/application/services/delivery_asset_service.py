from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
)


class DeliveryAssetService:
    def __init__(
        self, asset_repo: AssetRepositoryInterface,
    ):
        self.asset_repo = asset_repo

    def update_assets_on_delivery(
        self, shipment: Shipment,
    ) -> None:
        if (
            shipment.direction
            == ShipmentDirection.OUTBOUND
        ):
            if (
                shipment.destination_type
                == DestinationType.EMPLOYEE_HOME
            ):
                self._assign_assets(shipment)
        elif (
            shipment.direction
            == ShipmentDirection.INBOUND
        ):
            self._mark_assets_in_stock(shipment)

    def _assign_assets(
        self, shipment: Shipment,
    ) -> None:
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(
                item.asset_id, shipment.company_id,
            )
            if asset and shipment.recipient_user_id:
                asset.assign(
                    shipment.recipient_user_id,
                )
                self.asset_repo.save(asset)

    def _mark_assets_in_stock(
        self, shipment: Shipment,
    ) -> None:
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(
                item.asset_id, shipment.company_id,
            )
            if asset:
                asset.unassign()
                self.asset_repo.save(asset)
