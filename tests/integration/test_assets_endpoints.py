"""Integration tests for /api/v1/assets endpoints (TECHNICIAN)."""

import io
import pytest


class TestCreateAsset:
    def test_create_asset(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": "SN001",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["brand"] == "Dell"
        assert data["status"] == "in_stock"
        assert data["serial_number"] == "SN001"

    def test_create_asset_duplicate_serial(self, client, auth_as, technician_user):
        auth_as(technician_user)
        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "HP", "model": "EliteBook", "serial_number": "DUP001",
        })

        resp = client.post("/api/v1/assets", json={
            "type": "monitor", "brand": "LG", "model": "27UK850", "serial_number": "DUP001",
        })

        assert resp.status_code == 409

    def test_create_asset_with_dates(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "keyboard",
            "brand": "Logitech",
            "model": "MX Keys",
            "serial_number": "KB001",
            "purchase_date": "2024-01-15",
            "warranty_expiration": "2027-01-15",
            "notes": "Wireless keyboard",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["purchase_date"] == "2024-01-15"
        assert data["notes"] == "Wireless keyboard"


class TestListAssets:
    def test_list_assets(self, client, auth_as, technician_user):
        auth_as(technician_user)
        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "LIST001",
        })

        resp = client.get("/api/v1/assets")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    def test_list_assets_pagination(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/assets?page=1&page_size=5")

        assert resp.status_code == 200
        assert resp.json()["meta"]["page_size"] == 5

    def test_list_assets_filter_by_type(self, client, auth_as, technician_user):
        auth_as(technician_user)
        client.post("/api/v1/assets", json={
            "type": "monitor", "brand": "LG", "model": "M1", "serial_number": "FILT001",
        })

        resp = client.get("/api/v1/assets?type=monitor")

        assert resp.status_code == 200
        for a in resp.json()["data"]:
            assert a["type"] == "monitor"


class TestAssignableUsers:
    def test_list_assignable_users(self, client, auth_as, technician_user, employee_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/assets/assignable-users")

        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()["data"]]
        assert employee_user.email in emails


class TestGetAsset:
    def test_get_asset(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "XPS", "serial_number": "GET001",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/assets/{asset_id}")

        assert resp.status_code == 200
        assert resp.json()["data"]["serial_number"] == "GET001"

    def test_get_asset_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/assets/nonexistent")

        assert resp.status_code == 404


class TestUpdateAsset:
    def test_update_asset(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Old", "serial_number": "UPD001",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/assets/{asset_id}", json={"brand": "HP", "model": "New"})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["brand"] == "HP"
        assert data["model"] == "New"


class TestChangeAssetStatus:
    def test_change_status_to_in_repair(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "STAT001",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "in_repair"})

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "in_repair"

    def test_invalid_status_transition(self, client, auth_as, technician_user):
        """Decommissioned is terminal - cannot go back to in_stock."""
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "STAT002",
        })
        asset_id = create_resp.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "decommissioned"})

        resp = client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "in_stock"})

        assert resp.status_code == 409


class TestAssignAsset:
    def test_assign_asset(self, client, auth_as, technician_user, employee_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "ASGN001",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/assign", json={"user_id": employee_user.id})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["assigned_to"] == employee_user.id
        assert data["status"] == "assigned"

    def test_assign_non_stock_asset(self, client, auth_as, technician_user, employee_user):
        """Can only assign in_stock assets."""
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "ASGN002",
        })
        asset_id = create_resp.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "in_repair"})

        resp = client.patch(f"/api/v1/assets/{asset_id}/assign", json={"user_id": employee_user.id})

        assert resp.status_code == 409


class TestUnassignAsset:
    def test_unassign_asset(self, client, auth_as, technician_user, employee_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "UNASGN001",
        })
        asset_id = create_resp.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{asset_id}/assign", json={"user_id": employee_user.id})

        resp = client.patch(f"/api/v1/assets/{asset_id}/unassign")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["assigned_to"] is None
        assert data["status"] == "in_stock"

    def test_unassign_not_assigned(self, client, auth_as, technician_user):
        """Cannot unassign an asset that is not assigned."""
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "UNASGN002",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/assets/{asset_id}/unassign")

        assert resp.status_code == 409


class TestAssetHistory:
    def test_get_history(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "HIST001",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/assets/{asset_id}/history")

        assert resp.status_code == 200
        # Should have at least a "created" event
        assert isinstance(resp.json()["data"], list)


class TestImportAssets:
    def test_import_csv(self, client, auth_as, technician_user):
        auth_as(technician_user)
        csv_content = "type,brand,model,serial_number\nlaptop,Dell,Latitude,IMP001\nmonitor,LG,27UK850,IMP002"

        resp = client.post(
            "/api/v1/assets/import",
            files={"file": ("assets.csv", csv_content.encode(), "text/csv")},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert data["successful"] == 2

    def test_import_invalid_csv(self, client, auth_as, technician_user):
        auth_as(technician_user)
        csv_content = "bad_header1,bad_header2\nval1,val2"

        resp = client.post(
            "/api/v1/assets/import",
            files={"file": ("bad.csv", csv_content.encode(), "text/csv")},
        )

        assert resp.status_code == 422
