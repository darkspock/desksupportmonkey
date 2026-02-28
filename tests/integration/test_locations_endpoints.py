"""Integration tests for /api/v1/assets/locations endpoints (ADMIN)."""

import pytest


class TestListLocations:
    def test_list_locations(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/assets/locations")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        # Should have system locations seeded during company creation
        system_keys = [loc["system_key"] for loc in data if loc["is_system"]]
        assert "in_transit" in system_keys
        assert "main_warehouse" in system_keys

    def test_technician_can_list(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/assets/locations")

        assert resp.status_code == 200


class TestCreateLocation:
    def test_create_location(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/assets/locations", json={"name": "Server Room"})

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Server Room"
        assert data["is_system"] is False
        assert data["in_use"] is True

    def test_create_duplicate_name(self, client, auth_as, admin_user):
        auth_as(admin_user)
        client.post("/api/v1/assets/locations", json={"name": "Room A"})

        resp = client.post("/api/v1/assets/locations", json={"name": "Room A"})

        assert resp.status_code == 409

    def test_technician_cannot_create(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.post("/api/v1/assets/locations", json={"name": "Test"})

        assert resp.status_code == 403


class TestUpdateLocation:
    def test_update_location_name(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/assets/locations", json={"name": "Old Name"})
        loc_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/assets/locations/{loc_id}", json={"name": "New Name"})

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_update_in_use(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/assets/locations", json={"name": "Toggleable"})
        loc_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/assets/locations/{loc_id}", json={
            "name": "Toggleable", "in_use": False,
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["in_use"] is False

    def test_update_system_location_fails(self, client, auth_as, admin_user):
        auth_as(admin_user)
        # Get system locations
        list_resp = client.get("/api/v1/assets/locations")
        system_loc = next(
            loc for loc in list_resp.json()["data"] if loc["is_system"]
        )

        resp = client.put(
            f"/api/v1/assets/locations/{system_loc['id']}",
            json={"name": "Renamed"},
        )

        assert resp.status_code == 409

    def test_update_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.put("/api/v1/assets/locations/nonexistent", json={"name": "X"})

        assert resp.status_code == 404


class TestDeleteLocation:
    def test_delete_empty_location(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/assets/locations", json={"name": "Deletable"})
        loc_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"/api/v1/assets/locations/{loc_id}")

        assert resp.status_code == 204

    def test_delete_system_location_fails(self, client, auth_as, admin_user):
        auth_as(admin_user)
        list_resp = client.get("/api/v1/assets/locations")
        system_loc = next(
            loc for loc in list_resp.json()["data"] if loc["is_system"]
        )

        resp = client.delete(f"/api/v1/assets/locations/{system_loc['id']}")

        assert resp.status_code == 409

    def test_delete_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.delete("/api/v1/assets/locations/nonexistent")

        assert resp.status_code == 404


class TestMoveAsset:
    def test_move_asset(self, client, auth_as, technician_user, admin_user):
        auth_as(admin_user)
        # Create a custom location
        loc_resp = client.post("/api/v1/assets/locations", json={"name": "Room 42"})
        loc_id = loc_resp.json()["data"]["id"]

        auth_as(technician_user)
        # Create an asset
        asset_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "XPS", "serial_number": "MOV001",
        })
        asset_id = asset_resp.json()["data"]["id"]

        # Move asset to the new location
        resp = client.patch(f"/api/v1/assets/{asset_id}/move", json={
            "location_id": loc_id,
        })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["location_id"] == loc_id
        assert data["location_name"] == "Room 42"

    def test_move_asset_with_notes(self, client, auth_as, technician_user, admin_user):
        auth_as(admin_user)
        loc_resp = client.post("/api/v1/assets/locations", json={"name": "Room 43"})
        loc_id = loc_resp.json()["data"]["id"]

        auth_as(technician_user)
        asset_resp = client.post("/api/v1/assets", json={
            "type": "monitor", "brand": "LG", "model": "27", "serial_number": "MOV002",
        })
        asset_id = asset_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/move", json={
            "location_id": loc_id,
            "notes": "Relocated for project",
        })

        assert resp.status_code == 200

        # Verify in history
        history = client.get(f"/api/v1/assets/{asset_id}/history")
        events = history.json()["data"]
        location_events = [e for e in events if e["event_type"] == "location_changed"]
        assert len(location_events) >= 1
        assert location_events[0]["data"]["notes"] == "Relocated for project"

    def test_move_decommissioned_asset_fails(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Old", "serial_number": "MOV003",
        })
        asset_id = asset_resp.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "decommissioned"})

        # Get any location
        locs = client.get("/api/v1/assets/locations")
        loc_id = locs.json()["data"][0]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/move", json={
            "location_id": loc_id,
        })

        assert resp.status_code == 409

    def test_move_to_nonexistent_location_fails(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "X", "serial_number": "MOV004",
        })
        asset_id = asset_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/move", json={
            "location_id": "nonexistent-location",
        })

        assert resp.status_code == 404


class TestAssetLocationInResponse:
    def test_asset_list_shows_location(self, client, auth_as, technician_user):
        auth_as(technician_user)
        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Test", "serial_number": "LOC001",
        })

        resp = client.get("/api/v1/assets")

        assert resp.status_code == 200
        # All assets should have location_id field
        for asset in resp.json()["data"]:
            assert "location_id" in asset
            assert "location_name" in asset

    def test_asset_detail_shows_location(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "X", "serial_number": "LOC002",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/assets/{asset_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "location_id" in data
        assert "location_name" in data
