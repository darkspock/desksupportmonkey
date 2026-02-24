from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.commands.dispatch_shipment import (
    DispatchShipmentCommand,
    DispatchShipmentCommandHandler,
    ShipmentNotFoundError,
)
from src.shipping_bc.shipment.domain.entities import Shipment
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    InvalidShipmentStatusTransitionError,
    ShipmentDirection,
    ShipmentStatus,
)


def _make_draft_shipment(**overrides):
    defaults = dict(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_location_id="addr-1",
        created_by="user-1",
    )
    defaults.update(overrides)
    return Shipment.create(**defaults)


class TestDispatchShipment:
    def test_dispatch_sets_carrier_and_tracking(self):
        repo = MagicMock()
        shipment = _make_draft_shipment()
        repo.find_by_id.return_value = shipment
        handler = DispatchShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            DispatchShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                carrier="FedEx",
                tracking_number="FX123",
                tracking_url="https://track.fedex.com/FX123",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.DISPATCHED
        assert saved.carrier == "FedEx"
        assert saved.tracking_number == "FX123"
        assert saved.dispatched_at is not None

    def test_dispatch_without_carrier_raises(self):
        repo = MagicMock()
        shipment = _make_draft_shipment()
        repo.find_by_id.return_value = shipment
        handler = DispatchShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(ValueError, match="Carrier"):
            handler.handle(
                DispatchShipmentCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    performed_by="user-1",
                )
            )

    def test_dispatch_from_delivered_raises(self):
        repo = MagicMock()
        shipment = _make_draft_shipment(
            carrier="FedEx",
            tracking_number="FX123",
        )
        shipment.dispatch()
        shipment.deliver()
        repo.find_by_id.return_value = shipment
        handler = DispatchShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(
            InvalidShipmentStatusTransitionError,
        ):
            handler.handle(
                DispatchShipmentCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    performed_by="user-1",
                    carrier="UPS",
                    tracking_number="UPS456",
                )
            )
