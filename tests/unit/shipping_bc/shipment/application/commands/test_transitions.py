from unittest.mock import MagicMock

import pytest

from src.shipping_bc.shipment.application.commands.cancel_shipment import (
    CancelShipmentCommand,
    CancelShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.fail_shipment import (
    FailShipmentCommand,
    FailShipmentCommandHandler,
)
from src.shipping_bc.shipment.application.commands.mark_in_transit import (
    MarkInTransitCommand,
    MarkInTransitCommandHandler,
)
from src.shipping_bc.shipment.domain.entities import Shipment
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    InvalidShipmentStatusTransitionError,
    ShipmentDirection,
    ShipmentStatus,
)


def _make_dispatched_shipment():
    shipment = Shipment.create(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_location_id="addr-1",
        created_by="user-1",
        carrier="FedEx",
        tracking_number="FX123",
    )
    shipment.dispatch()
    return shipment


class TestMarkInTransit:
    def test_mark_in_transit(self):
        repo = MagicMock()
        shipment = _make_dispatched_shipment()
        repo.find_by_id.return_value = shipment
        handler = MarkInTransitCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            MarkInTransitCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.IN_TRANSIT


class TestFailShipment:
    def test_fail_with_reason(self):
        repo = MagicMock()
        shipment = _make_dispatched_shipment()
        repo.find_by_id.return_value = shipment
        handler = FailShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            FailShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                reason="Address incorrect",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.FAILED
        assert saved.failure_reason == "Address incorrect"


class TestCancelShipment:
    def test_cancel_with_reason(self):
        repo = MagicMock()
        shipment = Shipment.create(
            id="ship-1",
            company_id="comp-1",
            direction=ShipmentDirection.OUTBOUND,
            destination_type=DestinationType.EMPLOYEE_HOME,
            destination_location_id="addr-1",
            created_by="user-1",
        )
        repo.find_by_id.return_value = shipment
        handler = CancelShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            CancelShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                reason="No longer needed",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.status == ShipmentStatus.CANCELLED
        assert (
            saved.cancellation_reason == "No longer needed"
        )

    def test_cancel_from_terminal_raises(self):
        repo = MagicMock()
        shipment = _make_dispatched_shipment()
        shipment.deliver()
        repo.find_by_id.return_value = shipment
        handler = CancelShipmentCommandHandler(
            shipment_repo=repo,
        )

        with pytest.raises(
            InvalidShipmentStatusTransitionError,
        ):
            handler.handle(
                CancelShipmentCommand(
                    shipment_id="ship-1",
                    company_id="comp-1",
                    performed_by="user-1",
                    reason="Too late",
                )
            )
