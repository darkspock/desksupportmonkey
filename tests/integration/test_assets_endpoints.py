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


class TestSetCriticality:
    def _create_asset(self, client, serial):
        resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Latitude", "serial_number": serial,
        })
        return resp.json()["data"]["id"]

    def test_set_criticality(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "CRIT001")

        resp = client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": "critical"})

        assert resp.status_code == 200
        assert resp.json()["data"]["criticality"] == "critical"

    def test_set_criticality_high(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "CRIT002")

        resp = client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": "high"})

        assert resp.status_code == 200
        assert resp.json()["data"]["criticality"] == "high"

    def test_clear_criticality(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "CRIT003")
        client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": "medium"})

        resp = client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": None})

        assert resp.status_code == 200
        assert resp.json()["data"]["criticality"] is None

    def test_criticality_asset_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.patch("/api/v1/assets/nonexistent/criticality", json={"criticality": "high"})

        assert resp.status_code == 404

    def test_criticality_decommissioned(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "CRIT004")
        client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "decommissioned"})

        resp = client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": "critical"})

        assert resp.status_code == 422

    def test_criticality_event_recorded(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "CRIT005")

        client.patch(f"/api/v1/assets/{asset_id}/criticality", json={"criticality": "low"})

        history = client.get(f"/api/v1/assets/{asset_id}/history")
        events = history.json()["data"]
        crit_events = [e for e in events if e["event_type"] == "criticality_set"]
        assert len(crit_events) == 1
        assert crit_events[0]["data"]["new"] == "low"


class TestUpdateBia:
    def _create_asset(self, client, serial):
        resp = client.post("/api/v1/assets", json={
            "type": "server", "brand": "HP", "model": "ProLiant", "serial_number": serial,
        })
        return resp.json()["data"]["id"]

    def test_update_bia(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "BIA001")

        resp = client.patch(f"/api/v1/assets/{asset_id}/bia", json={
            "impact_score": 8,
            "rto_minutes": 240,
            "rpo_minutes": 60,
            "bia_justification": "Core database server",
        })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["impact_score"] == 8
        assert data["rto_minutes"] == 240
        assert data["rpo_minutes"] == 60
        assert data["bia_justification"] == "Core database server"
        assert data["bia_reviewed_at"] is not None
        assert data["bia_reviewed_by"] is not None

    def test_bia_invalid_impact_score(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "BIA002")

        resp = client.patch(f"/api/v1/assets/{asset_id}/bia", json={
            "impact_score": 11,
            "rto_minutes": 60,
            "rpo_minutes": 30,
        })

        assert resp.status_code == 422

    def test_bia_invalid_rto(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "BIA003")

        resp = client.patch(f"/api/v1/assets/{asset_id}/bia", json={
            "impact_score": 5,
            "rto_minutes": 0,
            "rpo_minutes": 30,
        })

        assert resp.status_code == 422

    def test_bia_asset_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.patch("/api/v1/assets/nonexistent/bia", json={
            "impact_score": 5, "rto_minutes": 60, "rpo_minutes": 30,
        })

        assert resp.status_code == 404

    def test_bia_decommissioned(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "BIA004")
        client.patch(f"/api/v1/assets/{asset_id}/status", json={"status": "decommissioned"})

        resp = client.patch(f"/api/v1/assets/{asset_id}/bia", json={
            "impact_score": 5, "rto_minutes": 60, "rpo_minutes": 30,
        })

        assert resp.status_code == 422

    def test_bia_event_recorded(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset_id = self._create_asset(client, "BIA005")

        client.patch(f"/api/v1/assets/{asset_id}/bia", json={
            "impact_score": 7, "rto_minutes": 120, "rpo_minutes": 0,
        })

        history = client.get(f"/api/v1/assets/{asset_id}/history")
        events = history.json()["data"]
        bia_events = [e for e in events if e["event_type"] == "bia_updated"]
        assert len(bia_events) == 1


class TestCriticalityFilter:
    def test_filter_by_criticality(self, client, auth_as, technician_user):
        auth_as(technician_user)
        # Create two assets with different criticalities
        r1 = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "FLTC001",
        })
        r2 = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M2", "serial_number": "FLTC002",
        })
        id1 = r1.json()["data"]["id"]
        id2 = r2.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{id1}/criticality", json={"criticality": "critical"})
        client.patch(f"/api/v1/assets/{id2}/criticality", json={"criticality": "low"})

        resp = client.get("/api/v1/assets?criticality=critical")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(a["criticality"] == "critical" for a in data)

    def test_get_asset_includes_new_fields(self, client, auth_as, technician_user):
        """GET /assets/{id} response includes criticality and BIA fields (null by default)."""
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "M1", "serial_number": "FLTC003",
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/assets/{asset_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["criticality"] is None
        assert data["impact_score"] is None
        assert data["rto_minutes"] is None
        assert data["rpo_minutes"] is None
        assert data["bia_justification"] is None
        assert data["bia_reviewed_at"] is None
        assert data["bia_reviewed_by"] is None
