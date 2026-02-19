from unittest.mock import MagicMock

from src.shipping_bc.shipment.application.commands.update_shipment import (
    UpdateShipmentCommand,
    UpdateShipmentCommandHandler,
)
from src.shipping_bc.shipment.domain.entities import Shipment
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    ShipmentDirection,
)


def _make_shipment():
    return Shipment.create(
        id="ship-1",
        company_id="comp-1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr-1",
        created_by="user-1",
    )


class TestUpdateShipment:
    def test_update_tracking_fields(self):
        repo = MagicMock()
        shipment = _make_shipment()
        repo.find_by_id.return_value = shipment
        handler = UpdateShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            UpdateShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                carrier="UPS",
                tracking_number="UPS789",
                tracking_url="https://ups.com/UPS789",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.carrier == "UPS"
        assert saved.tracking_number == "UPS789"
        assert saved.tracking_url == "https://ups.com/UPS789"

    def test_update_notes(self):
        repo = MagicMock()
        shipment = _make_shipment()
        repo.find_by_id.return_value = shipment
        handler = UpdateShipmentCommandHandler(
            shipment_repo=repo,
        )

        handler.handle(
            UpdateShipmentCommand(
                shipment_id="ship-1",
                company_id="comp-1",
                performed_by="user-1",
                notes="Handle with care",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.notes == "Handle with care"
        assert saved.carrier is None  # unchanged
