"""Integration tests for GET /api/v1/vendors/{vendor_id}/risk-profile."""


def _create_vendor(client, name="Test Vendor"):
    resp = client.post("/api/v1/vendors", json={"name": name})
    return resp.json()["data"]["id"]


def _create_contract(client, vendor_id, **overrides):
    payload = {
        "title": "Test Contract",
        "contract_type": "service",
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
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
        "business_function": "cloud_infrastructure",
        "is_critical": True,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/dependencies",
        json=payload,
    )


class TestGetVendorRiskProfile:
    def test_full_profile(self, client, auth_as, admin_user):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        # Create contract
        _create_contract(client, vendor_id)

        # Create assessment
        _create_assessment(client, vendor_id)

        # Create dependencies
        _create_dependency(client, vendor_id, is_critical=True)
        _create_dependency(
            client, vendor_id,
            service_description="Email",
            business_function="communications",
            is_critical=False,
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/risk-profile",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == vendor_id
        assert data["name"] == "Test Vendor"
        assert data["latest_assessment"] is not None
        assert data["latest_assessment"]["data_handling_score"] == 3
        assert data["latest_assessment"]["overall_risk_level"] == "high"
        assert data["total_contracts_count"] == 1
        assert data["dependency_count"] == 2
        assert data["critical_dependency_count"] == 1
        assert data["incident_count"] == 0
        assert data["risk_count"] == 0
        assert isinstance(data["incidents"], list)
        assert isinstance(data["risks"], list)

    def test_empty_vendor(self, client, auth_as, admin_user):
        auth_as(admin_user)
        vendor_id = _create_vendor(client, "Empty Vendor")

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/risk-profile",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["latest_assessment"] is None
        assert data["active_contracts_count"] == 0
        assert data["total_contracts_count"] == 0
        assert data["dependency_count"] == 0
        assert data["critical_dependency_count"] == 0
        assert data["incident_count"] == 0
        assert data["risk_count"] == 0

    def test_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get(
            "/api/v1/vendors/nonexistent/risk-profile",
        )
        assert resp.status_code == 404

    def test_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get(
            "/api/v1/vendors/any/risk-profile",
        )
        assert resp.status_code == 403

    def test_technician_allowed(
        self, client, auth_as, admin_user, technician_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        auth_as(technician_user)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/risk-profile",
        )
        assert resp.status_code == 200
