"""Integration tests for /api/v1/shipments endpoints."""

import pytest

from src.asset_bc.asset.domain.entities import AssetLocation
from src.asset_bc.asset.infrastructure.repository import AssetRepository


@pytest.fixture()
def shipment_location(db_session, company):
    """Create an asset location for integration tests."""
    loc = AssetLocation.create(
        company_id=company.id,
        name="HQ Office",
        street_line_1="123 Main St",
        city="Austin",
        state="TX",
        postal_code="78701",
        country="US",
    )
    repo = AssetRepository(db_session)
    repo.save_location(loc)
    db_session.flush()
    return loc


@pytest.fixture()
def second_location(db_session, company):
    """Create a second asset location."""
    loc = AssetLocation.create(
        company_id=company.id,
        name="Warehouse",
        street_line_1="456 Industrial Blvd",
        city="Austin",
        state="TX",
        postal_code="78702",
        country="US",
    )
    repo = AssetRepository(db_session)
    repo.save_location(loc)
    db_session.flush()
    return loc


def _create_asset(client, serial):
    """Create an asset and return its ID."""
    resp = client.post("/api/v1/assets", json={
        "type": "laptop",
        "brand": "Dell",
        "model": "Latitude 5520",
        "serial_number": serial,
    })
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_shipment(
    client, location_id, asset_ids,
    direction="OUTBOUND",
    destination_type="EMPLOYEE_HOME",
    **kwargs,
):
    """Create a shipment and return the response."""
    payload = {
        "direction": direction,
        "destination_type": destination_type,
        "destination_location_id": location_id,
        "asset_ids": asset_ids,
        **kwargs,
    }
    return client.post("/api/v1/shipments", json=payload)


class TestCreateShipment:
    def test_create_shipment_returns_201(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN001")

        resp = _create_shipment(
            client,
            shipment_location.id,
            [asset_id],
            service_level="two_day",
            items_description="Laptop + Dock",
            internal_notes="Handle with care",
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "DRAFT"
        assert data["direction"] == "OUTBOUND"
        assert data["item_count"] == 1
        assert len(data["items"]) == 1
        assert data["service_level"] == "two_day"
        assert data["items_description"] == "Laptop + Dock"
        assert data["internal_notes"] == "Handle with care"

    def test_create_with_asset_conflict_returns_409(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN002")

        # First shipment — OK
        resp1 = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        assert resp1.status_code == 201

        # Second with same asset — conflict
        resp2 = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        assert resp2.status_code == 409


class TestListShipments:
    def test_list_shipments_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN003")
        _create_shipment(
            client, shipment_location.id, [asset_id],
        )

        resp = client.get("/api/v1/shipments")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1


class TestGetShipment:
    def test_get_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN004")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/shipments/{sid}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == sid


class TestUpdateShipment:
    def test_update_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN005")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/shipments/{sid}",
            json={
                "carrier": "FedEx",
                "tracking_number": "FX999",
                "service_level": "overnight",
                "items_description": "Laptop only",
                "internal_notes": "Deliver before 10am",
                "notes": "Rush delivery",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["carrier"] == "FedEx"
        assert data["service_level"] == "overnight"
        assert data["items_description"] == "Laptop only"
        assert data["internal_notes"] == "Deliver before 10am"
        assert data["notes"] == "Rush delivery"


class TestDispatchShipment:
    def test_dispatch_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN006")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "UPS",
                "tracking_number": "UPS123",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "DISPATCHED"

    def test_dispatch_without_tracking_returns_422(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN007")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={},
        )
        assert resp.status_code == 422


class TestMarkInTransit:
    def test_mark_in_transit_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN008")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        # Dispatch first
        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "FedEx",
                "tracking_number": "FX100",
            },
        )

        resp = client.post(
            f"/api/v1/shipments/{sid}/in-transit",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "IN_TRANSIT"


class TestDeliverShipment:
    def test_deliver_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN009")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "DHL",
                "tracking_number": "DHL001",
            },
        )

        resp = client.post(
            f"/api/v1/shipments/{sid}/deliver",
            json={"notes": "Left at door"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "DELIVERED"
        assert data["notes"] == "Left at door"


class TestFailShipment:
    def test_fail_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN010")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "FedEx",
                "tracking_number": "FX200",
            },
        )

        resp = client.post(
            f"/api/v1/shipments/{sid}/fail",
            json={"reason": "Wrong address"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "FAILED"
        assert data["failure_reason"] == "Wrong address"


class TestCancelShipment:
    def test_cancel_shipment_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN011")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/shipments/{sid}/cancel",
            json={"reason": "Order cancelled"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "CANCELLED"
        assert data["cancellation_reason"] == "Order cancelled"

    def test_invalid_transition_returns_409(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN012")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        # Dispatch and deliver
        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "UPS",
                "tracking_number": "UPS100",
            },
        )
        client.post(
            f"/api/v1/shipments/{sid}/deliver",
            json={},
        )

        # Cancel delivered → 409
        resp = client.post(
            f"/api/v1/shipments/{sid}/cancel",
            json={"reason": "Too late"},
        )
        assert resp.status_code == 409


class TestCreateReturn:
    def test_create_return_returns_201(
        self, client, auth_as, technician_user,
        shipment_location, second_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN013")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
        )
        sid = create_resp.json()["data"]["id"]

        # Dispatch and deliver the original
        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "FedEx",
                "tracking_number": "FX300",
            },
        )
        client.post(
            f"/api/v1/shipments/{sid}/deliver",
            json={},
        )

        resp = client.post(
            f"/api/v1/shipments/{sid}/return",
            json={
                "destination_location_id": second_location.id,
                "asset_ids": [asset_id],
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["direction"] == "INBOUND"
        assert data["return_for_shipment_id"] == sid


class TestShipmentsByAsset:
    def test_shipments_by_asset_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN014")
        _create_shipment(
            client, shipment_location.id, [asset_id],
        )

        resp = client.get(
            f"/api/v1/shipments/by-asset/{asset_id}",
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestModifyItems:
    def test_modify_items_returns_200(
        self, client, auth_as, technician_user,
        shipment_location,
    ):
        auth_as(technician_user)
        asset1 = _create_asset(client, "SHIP-SN015")
        asset2 = _create_asset(client, "SHIP-SN016")
        create_resp = _create_shipment(
            client, shipment_location.id, [asset1],
        )
        sid = create_resp.json()["data"]["id"]
        item_id = create_resp.json()["data"]["items"][0]["id"]

        resp = client.patch(
            f"/api/v1/shipments/{sid}/items",
            json={
                "add_asset_ids": [asset2],
                "remove_item_ids": [item_id],
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["item_count"] == 1
        assert data["items"][0]["asset_id"] == asset2


class TestMyShipments:
    def test_my_shipments_returns_200(
        self, client, auth_as, technician_user,
        employee_user, shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN017")
        _create_shipment(
            client, shipment_location.id, [asset_id],
            recipient_user_id=employee_user.id,
        )

        auth_as(employee_user)
        resp = client.get("/api/v1/my/shipments")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body


class TestDashboardShipments:
    def test_dashboard_shipments_returns_200(
        self, client, auth_as, admin_user,
        technician_user, shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN018")
        _create_shipment(
            client, shipment_location.id, [asset_id],
        )

        auth_as(admin_user)
        resp = client.get(
            "/api/v1/dashboard/shipments/summary",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "active_by_status" in data
        assert "recent_deliveries" in data
        assert "failed_count" in data


class TestDeliverOutboundEmployeeAssignsAssets:
    def test_deliver_outbound_employee_assigns_assets(
        self, client, auth_as, technician_user,
        employee_user, shipment_location,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "SHIP-SN019")

        # Create outbound to employee home
        create_resp = _create_shipment(
            client, shipment_location.id, [asset_id],
            direction="OUTBOUND",
            destination_type="EMPLOYEE_HOME",
            recipient_user_id=employee_user.id,
        )
        sid = create_resp.json()["data"]["id"]

        # Dispatch
        client.post(
            f"/api/v1/shipments/{sid}/dispatch",
            json={
                "carrier": "FedEx",
                "tracking_number": "FX400",
            },
        )

        # Deliver — should assign asset to employee
        resp = client.post(
            f"/api/v1/shipments/{sid}/deliver",
            json={},
        )
        assert resp.status_code == 200

        # Verify asset is now assigned
        asset_resp = client.get(f"/api/v1/assets/{asset_id}")
        assert asset_resp.status_code == 200
        asset_data = asset_resp.json()["data"]
        assert asset_data["status"] == "assigned"
        assert asset_data["assigned_to"] == employee_user.id
