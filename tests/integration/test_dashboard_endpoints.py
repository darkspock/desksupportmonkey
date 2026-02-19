"""Integration tests for /api/v1/dashboard endpoints (ADMIN)."""

import pytest


class TestRequestSummary:
    def test_request_summary_empty(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/summary")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "by_status" in data
        assert "by_type" in data
        assert "by_priority" in data
        assert "total_open" in data
        assert "total_resolved" in data

    def test_request_summary_with_data(self, client, auth_as, admin_user, employee_user):
        # Create a request as employee
        auth_as(employee_user)
        client.post("/api/v1/requests", json={
            "type": "incident", "title": "Issue", "description": "Desc",
        })

        auth_as(admin_user)
        resp = client.get("/api/v1/dashboard/requests/summary")

        assert resp.status_code == 200
        assert resp.json()["data"]["total_open"] >= 1


class TestResolutionTime:
    def test_resolution_time(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/resolution-time")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "avg_hours" in data
        assert "by_technician" in data

    def test_resolution_time_with_dates(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/resolution-time?from_date=2024-01-01&to_date=2024-12-31")

        assert resp.status_code == 200


class TestRequestTrend:
    def test_trend_daily(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/trend?bucket=day")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["bucket"] == "day"
        assert "from_date" in data
        assert "to_date" in data

    def test_trend_weekly(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/trend?bucket=week")

        assert resp.status_code == 200

    def test_trend_monthly(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/requests/trend?bucket=month")

        assert resp.status_code == 200


class TestAssetSummary:
    def test_asset_summary_empty(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/assets/summary")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "by_status" in data
        assert "by_type" in data
        assert "total" in data

    def test_asset_summary_with_data(self, client, auth_as, admin_user, technician_user):
        auth_as(technician_user)
        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "XPS", "serial_number": "DASH001",
        })

        auth_as(admin_user)
        resp = client.get("/api/v1/dashboard/assets/summary")

        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1


class TestWarrantyAlerts:
    def test_warranty_alerts(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/alerts/warranty")

        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_warranty_alerts_custom_days(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/alerts/warranty?days=90")

        assert resp.status_code == 200


class TestAgingAlerts:
    def test_aging_alerts(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/alerts/aging")

        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


class TestSlaAlerts:
    def test_sla_alerts(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/alerts/sla")

        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


class TestBudgetHealth:
    def test_budget_health_empty(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/dashboard/budget-health")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_allocated_cents" in data
        assert "total_spent_cents" in data
        assert "departments_at_risk" in data
        assert data["total_allocated_cents"] == 0
        assert data["total_spent_cents"] == 0

    def test_budget_health_admin_only(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/dashboard/budget-health")

        assert resp.status_code == 403


class TestRecentPurchaseOrders:
    def test_recent_pos_empty(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/dashboard/recent-purchase-orders")

        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        assert len(resp.json()["data"]) == 0

    def test_recent_pos_with_data(self, client, auth_as, admin_user, technician_user, db_session):
        # Create a department first
        auth_as(admin_user)
        dept_resp = client.post("/api/v1/departments", json={"name": "PO Test Dept"})
        dept_id = dept_resp.json()["data"]["id"]

        # Create a PO as technician
        auth_as(technician_user)
        po_resp = client.post("/api/v1/purchase-orders", json={
            "vendor_name": "Test Vendor",
            "department_id": dept_id,
            "items": [{"description": "Test Item", "quantity": 1, "unit_cost_cents": 5000}],
        })
        assert po_resp.status_code == 201

        resp = client.get("/api/v1/dashboard/recent-purchase-orders")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["vendor_name"] == "Test Vendor"
