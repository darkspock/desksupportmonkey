"""Integration tests for /api/v1/maintenance endpoints."""


def _create_asset(client, serial):
    resp = client.post(
        "/api/v1/assets",
        json={
            "type": "laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": serial,
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_maintenance(client, asset_id, technician_id):
    return client.post(
        "/api/v1/maintenance",
        json={
            "asset_id": asset_id,
            "title": "Battery check",
            "priority": "HIGH",
            "technician_id": technician_id,
            "checklist_items": ["Inspect", "Clean"],
        },
    )


class TestMaintenanceCRUD:
    def test_create_and_get(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN001")

        create_resp = _create_maintenance(
            client,
            asset_id,
            technician_user.id,
        )
        assert create_resp.status_code == 201
        record_id = create_resp.json()["data"]["id"]
        assert create_resp.json()["data"]["status"] == "SCHEDULED"

        get_resp = client.get(f"/api/v1/maintenance/{record_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == record_id

    def test_list(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN002")
        _create_maintenance(client, asset_id, technician_user.id)

        resp = client.get("/api/v1/maintenance")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1

    def test_update_when_scheduled(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN003")
        create_resp = _create_maintenance(client, asset_id, technician_user.id)
        record_id = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/maintenance/{record_id}",
            json={"title": "Battery check updated", "priority": "CRITICAL"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Battery check updated"
        assert resp.json()["data"]["priority"] == "CRITICAL"


class TestMaintenanceActions:
    def test_start_complete_flow(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN004")
        create_resp = _create_maintenance(client, asset_id, technician_user.id)
        record_id = create_resp.json()["data"]["id"]

        start_resp = client.post(f"/api/v1/maintenance/{record_id}/start")
        assert start_resp.status_code == 200
        assert start_resp.json()["data"]["status"] == "IN_PROGRESS"

        complete_resp = client.post(
            f"/api/v1/maintenance/{record_id}/complete",
            json={"completion_notes": "Done", "actual_findings": "OK"},
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["data"]["status"] == "COMPLETED"

    def test_cancel(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN005")
        create_resp = _create_maintenance(client, asset_id, technician_user.id)
        record_id = create_resp.json()["data"]["id"]

        cancel_resp = client.post(
            f"/api/v1/maintenance/{record_id}/cancel",
            json={"reason": "No longer needed"},
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["data"]["status"] == "CANCELLED"


class TestMaintenanceAggregates:
    def test_my_maintenance_queue(
        self,
        client,
        auth_as,
        technician_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN006")
        _create_maintenance(client, asset_id, technician_user.id)

        resp = client.get("/api/v1/my/maintenance")
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    def test_dashboard_summary(
        self,
        client,
        auth_as,
        technician_user,
        admin_user,
    ):
        auth_as(technician_user)
        asset_id = _create_asset(client, "M-SN007")
        _create_maintenance(client, asset_id, technician_user.id)

        auth_as(admin_user)
        resp = client.get("/api/v1/dashboard/maintenance")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "scheduled" in data
        assert "overdue" in data
        assert "in_progress" in data
        assert "completed_30d" in data
