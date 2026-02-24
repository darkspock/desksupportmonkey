import logging

from src.asset_bc.asset.domain.entities import (
    InvalidAssignmentError,
)
from src.asset_bc.asset.domain.enums import (
    SystemLocation,
)
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

logger = logging.getLogger(__name__)


class DeliveryAssetService:
    def __init__(
        self, asset_repo: AssetRepositoryInterface,
    ):
        self.asset_repo = asset_repo

    def update_assets_on_dispatch(
        self, shipment: Shipment,
    ) -> None:
        """Move all shipment assets to 'In Transit' on dispatch."""
        transit_loc = self.asset_repo.find_system_location(
            shipment.company_id,
            SystemLocation.IN_TRANSIT.value,
        )
        if not transit_loc:
            return
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(
                item.asset_id, shipment.company_id,
            )
            if asset:
                asset.location_id = transit_loc.id
                self.asset_repo.save(asset)

    def update_assets_on_delivery(
        self, shipment: Shipment,
    ) -> None:
        """Move assets to destination location and handle assign/unassign."""
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(
                item.asset_id, shipment.company_id,
            )
            if not asset:
                continue

            # Always move to destination location
            if shipment.destination_location_id:
                asset.location_id = (
                    shipment.destination_location_id
                )

            # Auto-assign for outbound EMPLOYEE_HOME
            if (
                shipment.direction
                == ShipmentDirection.OUTBOUND
                and shipment.destination_type
                == DestinationType.EMPLOYEE_HOME
                and shipment.recipient_user_id
            ):
                try:
                    asset.assign(
                        shipment.recipient_user_id,
                    )
                except InvalidAssignmentError:
                    logger.warning(
                        "Cannot assign asset %s (status=%s), skipping",
                        asset.id,
                        asset.status,
                    )
            # Auto-unassign for inbound
            elif (
                shipment.direction
                == ShipmentDirection.INBOUND
            ):
                try:
                    asset.unassign()
                except InvalidAssignmentError:
                    logger.warning(
                        "Cannot unassign asset %s (status=%s), skipping",
                        asset.id,
                        asset.status,
                    )

            self.asset_repo.save(asset)
