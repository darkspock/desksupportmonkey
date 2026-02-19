from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.commands.create_shipment import (
    AssetConflictError,
    CreateShipmentCommand,
    CreateShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.create_return_shipment import (
    CreateReturnShipmentCommand,
    CreateReturnShipmentCommandHandler,
    ShipmentNotFoundError,
)
from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
    ShipmentStatus,
)


def _make_shipment(**overrides):
    defaults = dict(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr-1",
        created_by="user-1",
    )
    defaults.update(overrides)
    return Shipment.create(**defaults)


class TestCreateShipment:
    def test_create_shipment_saves_draft(self):
        repo = MagicMock()
        repo.find_active_by_asset_id.return_value = []
        handler = CreateShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            CreateShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                direction="OUTBOUND",
                destination_type="EMPLOYEE_HOME",
                destination_address_id="addr-1",
                created_by="user-1",
                asset_ids=["asset-1", "asset-2"],
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.DRAFT
        assert len(saved.items) == 2

    def test_create_validates_asset_conflict(self):
        repo = MagicMock()
        existing = _make_shipment(id="other-ship")
        repo.find_active_by_asset_id.return_value = [
            existing,
        ]
        handler = CreateShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(AssetConflictError):
            handler.handle(
                CreateShipmentCommand(
                    shipment_id="ship-2",
                    company_id="comp-1",
                    direction="OUTBOUND",
                    destination_type="EMPLOYEE_HOME",
                    destination_address_id="addr-1",
                    created_by="user-1",
                    asset_ids=["asset-1"],
                )
            )

    def test_create_validates_direction(self):
        repo = MagicMock()
        handler = CreateShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(ValueError):
            handler.handle(
                CreateShipmentCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    direction="INVALID",
                    destination_type="EMPLOYEE_HOME",
                    destination_address_id="addr-1",
                    created_by="user-1",
                    asset_ids=[],
                )
            )


class TestCreateReturnShipment:
    def test_create_return_links_original(self):
        repo = MagicMock()
        original = _make_shipment(id="ship-orig")
        repo.find_by_id.return_value = original
        repo.find_active_by_asset_id.return_value = []
        handler = CreateReturnShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            CreateReturnShipmentCommand(
                return_shipment_id="ship-ret",
                original_shipment_id="ship-orig",
                company_id="comp-1",
                created_by="user-1",
                destination_address_id="addr-2",
                asset_ids=["asset-1"],
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.return_for_shipment_id == "ship-orig"
        assert saved.direction == ShipmentDirection.INBOUND
        assert saved.origin_address_id == "addr-1"

    def test_create_return_original_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = CreateReturnShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(ShipmentNotFoundError):
            handler.handle(
                CreateReturnShipmentCommand(
                    return_shipment_id="ship-ret",
                    original_shipment_id="ship-nope",
                    company_id="comp-1",
                    created_by="user-1",
                    destination_address_id="addr-2",
                    asset_ids=["asset-1"],
                )
            )
