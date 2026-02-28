"""Integration tests for vendor supply chain dashboard and export endpoints."""


def _create_vendor(client, name="Test Vendor", **overrides):
    payload = {"name": name}
    payload.update(overrides)
    resp = client.post("/api/v1/vendors", json=payload)
    return resp.json()["data"]["id"]


def _create_contract(client, vendor_id, **overrides):
    payload = {
        "title": "Test Contract",
        "contract_type": "service",
        "start_date": "2026-01-01",
        "end_date": "2026-04-01",
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/contracts",
        json=payload,
    )


def _create_assessment(client, vendor_id, **overrides):
    payload = {
        "assessment_date": "2026-02-26",
        "data_handling_score": 3,
        "security_certs_score": 4,
        "incident_response_score": 3,
        "business_continuity_score": 4,
        "subcontractor_score": 3,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/assessments",
        json=payload,
    )


def _create_dependency(client, vendor_id, **overrides):
    payload = {
        "service_description": "Cloud hosting",
        "business_function": "it_infrastructure",
        "is_critical": True,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/dependencies",
        json=payload,
    )


class TestSupplyChainDashboard:
    def test_dashboard_with_data(self, client, auth_as, admin_user):
        auth_as(admin_user)
        vendor_id = _create_vendor(client, "DashVendor")
        _create_contract(client, vendor_id)
        _create_assessment(client, vendor_id)
        _create_dependency(client, vendor_id)

        resp = client.get("/api/v1/vendors/supply-chain-dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_vendors"] >= 1
        assert data["active_vendors"] >= 1
        assert isinstance(data["vendors_by_risk_level"], dict)
        assert isinstance(data["expiring_contracts"], list)
        assert isinstance(data["concentration_risk_items"], list)

    def test_dashboard_empty_company(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/vendors/supply-chain-dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_vendors"] >= 0

    def test_dashboard_employee_forbidden(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.get("/api/v1/vendors/supply-chain-dashboard")
        assert resp.status_code == 403

    def test_dashboard_technician_allowed(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.get("/api/v1/vendors/supply-chain-dashboard")
        assert resp.status_code == 200


class TestExportVendorRisk:
    def test_export_csv_accepted(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/vendors/risk-export",
            json={"format": "csv"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["format"] == "csv"
        assert "storage_key" in data

    def test_export_pdf_accepted(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/vendors/risk-export",
            json={"format": "pdf"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["format"] == "pdf"

    def test_export_employee_forbidden(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/vendors/risk-export",
            json={"format": "csv"},
        )
        assert resp.status_code == 403

    def test_export_technician_forbidden(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/vendors/risk-export",
            json={"format": "csv"},
        )
        assert resp.status_code == 403

    def test_export_invalid_format(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/vendors/risk-export",
            json={"format": "xlsx"},
        )
        assert resp.status_code == 422
