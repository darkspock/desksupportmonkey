import pytest

from src.shipping_bc.shipment.domain.entities import (
    Shipment,
    ShipmentItem,
    MAX_ITEMS_PER_SHIPMENT,
)
from src.shipping_bc.shipment.domain.enums import (
    DestinationType,
    InvalidShipmentStatusTransitionError,
    ShipmentDirection,
    ShipmentStatus,
)


def _make_shipment(**overrides):
    defaults = dict(
        company_id="comp1",
        direction=ShipmentDirection.OUTBOUND,
        destination_type=DestinationType.EMPLOYEE_HOME,
        destination_address_id="addr1",
        created_by="user1",
    )
    defaults.update(overrides)
    return Shipment.create(**defaults)


class TestShipmentCreate:

    def test_create_generates_ulid_and_draft_status(
        self,
    ):
        s = _make_shipment()
        assert s.id is not None
        assert len(s.id) == 26
        assert s.status == ShipmentStatus.DRAFT

    def test_create_validates_items_count(self):
        items = [
            ShipmentItem.create(
                shipment_id="s1", asset_id=f"a{i}",
            )
            for i in range(MAX_ITEMS_PER_SHIPMENT + 1)
        ]
        with pytest.raises(ValueError, match="20"):
            _make_shipment(items=items)


class TestShipmentDispatch:

    def test_dispatch_from_draft(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        assert s.status == ShipmentStatus.DISPATCHED
        assert s.dispatched_at is not None

    def test_dispatch_without_carrier_raises(self):
        s = _make_shipment(tracking_number="123")
        with pytest.raises(
            ValueError, match="Carrier",
        ):
            s.dispatch()

    def test_dispatch_without_tracking_raises(self):
        s = _make_shipment(carrier="FedEx")
        with pytest.raises(
            ValueError, match="Tracking",
        ):
            s.dispatch()

    def test_dispatch_from_delivered_raises(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.deliver()
        with pytest.raises(
            InvalidShipmentStatusTransitionError,
        ):
            s.dispatch()


class TestShipmentInTransit:

    def test_mark_in_transit_from_dispatched(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.mark_in_transit()
        assert s.status == ShipmentStatus.IN_TRANSIT

    def test_mark_in_transit_from_draft_raises(self):
        s = _make_shipment()
        with pytest.raises(
            InvalidShipmentStatusTransitionError,
        ):
            s.mark_in_transit()


class TestShipmentDeliver:

    def test_deliver_from_dispatched(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.deliver()
        assert s.status == ShipmentStatus.DELIVERED
        assert s.delivered_at is not None

    def test_deliver_from_in_transit(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.mark_in_transit()
        s.deliver()
        assert s.status == ShipmentStatus.DELIVERED
        assert s.delivered_at is not None


class TestShipmentFail:

    def test_fail_from_dispatched(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.fail("Package lost")
        assert s.status == ShipmentStatus.FAILED
        assert s.failure_reason == "Package lost"

    def test_fail_from_in_transit(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.mark_in_transit()
        s.fail("Damaged")
        assert s.status == ShipmentStatus.FAILED
        assert s.failure_reason == "Damaged"


class TestShipmentCancel:

    def test_cancel_from_draft(self):
        s = _make_shipment()
        s.cancel("No longer needed")
        assert s.status == ShipmentStatus.CANCELLED
        assert (
            s.cancellation_reason == "No longer needed"
        )

    def test_cancel_from_dispatched(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.cancel("Wrong address")
        assert s.status == ShipmentStatus.CANCELLED

    def test_cancel_from_delivered_raises(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        s.deliver()
        with pytest.raises(
            InvalidShipmentStatusTransitionError,
        ):
            s.cancel("Oops")


class TestShipmentItems:

    def test_add_item_in_draft(self):
        s = _make_shipment()
        item = ShipmentItem.create(
            shipment_id=s.id, asset_id="asset1",
        )
        s.add_item(item)
        assert len(s.items) == 1

    def test_add_item_in_dispatched_raises(self):
        s = _make_shipment(
            carrier="FedEx",
            tracking_number="123",
        )
        s.dispatch()
        item = ShipmentItem.create(
            shipment_id=s.id, asset_id="asset1",
        )
        with pytest.raises(
            ValueError, match="DRAFT",
        ):
            s.add_item(item)

    def test_remove_item_in_draft(self):
        item = ShipmentItem.create(
            shipment_id="s1", asset_id="asset1",
        )
        s = _make_shipment(items=[item])
        assert len(s.items) == 1
        s.remove_item(item.id)
        assert len(s.items) == 0


class TestShipmentStatusProperties:

    def test_is_terminal(self):
        assert ShipmentStatus.DELIVERED.is_terminal
        assert ShipmentStatus.FAILED.is_terminal
        assert ShipmentStatus.CANCELLED.is_terminal
        assert not ShipmentStatus.DRAFT.is_terminal
        assert not ShipmentStatus.DISPATCHED.is_terminal
        assert not ShipmentStatus.IN_TRANSIT.is_terminal

    def test_is_active(self):
        assert ShipmentStatus.DRAFT.is_active
        assert ShipmentStatus.DISPATCHED.is_active
        assert ShipmentStatus.IN_TRANSIT.is_active
        assert not ShipmentStatus.DELIVERED.is_active
        assert not ShipmentStatus.FAILED.is_active
        assert not ShipmentStatus.CANCELLED.is_active
