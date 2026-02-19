from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.commands.create_shipment import (
    AssetConflictError,
)
from src.shipping_bc.shipment.application.commands.modify_shipment_items import (
    ModifyShipmentItemsCommand,
    ModifyShipmentItemsCommandHandler,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
)


def _make_draft_with_items():
    item = ShipmentItem.create(
        shipment_id="ship-1", asset_id="asset-1",
        id="item-1",
    )
    return Shipment.create(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr-1",
        created_by="user-1",
        items=[item],
    )


class TestModifyShipmentItems:
    def test_modify_add_items_in_draft(self):
        repo = MagicMock()
        shipment = _make_draft_with_items()
        repo.find_by_id.return_value = shipment
        repo.find_active_by_asset_id.return_value = []
        handler = ModifyShipmentItemsCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            ModifyShipmentItemsCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                add_asset_ids=["asset-2"],
            )
        )

        saved = repo.save.call_args[0][0]
        assert len(saved.items) == 2

    def test_modify_remove_items_in_draft(self):
        repo = MagicMock()
        shipment = _make_draft_with_items()
        repo.find_by_id.return_value = shipment
        handler = ModifyShipmentItemsCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            ModifyShipmentItemsCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                remove_item_ids=["item-1"],
            )
        )

        saved = repo.save.call_args[0][0]
        assert len(saved.items) == 0

    def test_modify_in_dispatched_raises(self):
        repo = MagicMock()
        shipment = Shipment.create(
            id="ship-1",
            company_id="comp-1",
            direction=ShipmentDirection.OUTBOUND,
            destination_type=DestinationType.EMPLOYEE_HOME,
            destination_address_id="addr-1",
            created_by="user-1",
            carrier="FedEx",
            tracking_number="FX123",
        )
        shipment.dispatch()
        repo.find_by_id.return_value = shipment
        handler = ModifyShipmentItemsCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(ValueError, match="DRAFT"):
            handler.handle(
                ModifyShipmentItemsCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    performed_by="user-1",
                    add_asset_ids=["asset-2"],
                )
            )

    def test_modify_validates_asset_conflict(self):
        repo = MagicMock()
        shipment = _make_draft_with_items()
        repo.find_by_id.return_value = shipment
        other_shipment = Shipment.create(
            id="ship-other",
            company_id="comp-1",
            direction=ShipmentDirection.OUTBOUND,
            destination_type=DestinationType.OFFICE,
            destination_address_id="addr-2",
            created_by="user-1",
        )
        repo.find_active_by_asset_id.return_value = [
            other_shipment,
        ]
        handler = ModifyShipmentItemsCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(AssetConflictError):
            handler.handle(
                ModifyShipmentItemsCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    performed_by="user-1",
                    add_asset_ids=["asset-2"],
                )
            )
