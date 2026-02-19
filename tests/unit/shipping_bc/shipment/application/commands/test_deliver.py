from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.commands.deliver_shipment import (
    DeliverShipmentCommand,
    DeliverShipmentCommandHandler,
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


def _make_dispatched_shipment(**overrides):
    defaults = dict(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr-1",
        created_by="user-1",
        carrier="FedEx",
        tracking_number="FX123",
        recipient_user_id="emp-1",
        items=[
            ShipmentItem.create(
                shipment_id="ship-1",
                asset_id="asset-1",
            ),
        ],
    )
    defaults.update(overrides)
    shipment = Shipment.create(**defaults)
    shipment.dispatch()
    return shipment


class TestDeliverShipment:
    def test_deliver_from_dispatched(self):
        repo = MagicMock()
        delivery_service = MagicMock()
        shipment = _make_dispatched_shipment()
        repo.find_by_id.return_value = shipment
        handler = DeliverShipmentCommandHandler(
            shipment_repo=repo,
            delivery_asset_service=delivery_service,
        )

        handler.handle(
            DeliverShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.DELIVERED
        assert saved.delivered_at is not None

    def test_deliver_from_in_transit(self):
        repo = MagicMock()
        delivery_service = MagicMock()
        shipment = _make_dispatched_shipment()
        shipment.mark_in_transit()
        repo.find_by_id.return_value = shipment
        handler = DeliverShipmentCommandHandler(
            shipment_repo=repo,
            delivery_asset_service=delivery_service,
        )

        handler.handle(
            DeliverShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.DELIVERED

    def test_deliver_calls_asset_service_employee_home(
        self,
    ):
        repo = MagicMock()
        delivery_service = MagicMock()
        shipment = _make_dispatched_shipment()
        repo.find_by_id.return_value = shipment
        handler = DeliverShipmentCommandHandler(
            shipment_repo=repo,
            delivery_asset_service=delivery_service,
        )

        handler.handle(
            DeliverShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
            )
        )

        delivery_service.update_assets_on_delivery.assert_called_once()

    def test_deliver_calls_asset_service_for_office(
        self,
    ):
        repo = MagicMock()
        delivery_service = MagicMock()
        shipment = _make_dispatched_shipment(
            destination_type=DestinationType.OFFICE,
        )
        repo.find_by_id.return_value = shipment
        handler = DeliverShipmentCommandHandler(
            shipment_repo=repo,
            delivery_asset_service=delivery_service,
        )

        handler.handle(
            DeliverShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
            )
        )

        # Service is always called; it decides internally
        # whether to act based on direction+destination_type
        delivery_service.update_assets_on_delivery.assert_called_once()
