"""Integration tests for /api/v1/vendors/{vendor_id}/assessments."""


def _create_vendor(client, name="Test Vendor"):
    resp = client.post(
        "/api/v1/vendors",
        json={"name": name},
    )
    return resp.json()["data"]["id"]


def _create_assessment(client, vendor_id, **overrides):
    payload = {
        "assessment_date": "2026-02-26",
        "data_handling_score": 3,
        "security_certs_score": 3,
        "incident_response_score": 3,
        "business_continuity_score": 3,
        "subcontractor_score": 3,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/assessments",
        json=payload,
    )


class TestCreateAssessment:
    def test_create_assessment_admin(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_assessment(client, vendor_id)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["overall_risk_level"] == "medium"
        assert data["data_handling_score"] == 3
        assert data["vendor_id"] == vendor_id

    def test_create_calculates_low_risk(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_assessment(
            client, vendor_id,
            data_handling_score=1,
            security_certs_score=1,
            incident_response_score=1,
            business_continuity_score=1,
            subcontractor_score=1,
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["overall_risk_level"] == "low"

    def test_create_calculates_critical_risk(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_assessment(
            client, vendor_id,
            data_handling_score=5,
            security_certs_score=5,
            incident_response_score=5,
            business_continuity_score=5,
            subcontractor_score=5,
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["overall_risk_level"] == "critical"

    def test_create_updates_vendor_risk_level(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        _create_assessment(
            client, vendor_id,
            data_handling_score=4,
            security_certs_score=4,
            incident_response_score=4,
            business_continuity_score=4,
            subcontractor_score=4,
        )

        vendor_resp = client.get(f"/api/v1/vendors/{vendor_id}")
        assert vendor_resp.json()["data"]["risk_level"] == "high"

    def test_create_vendor_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = _create_assessment(client, "nonexistent")
        assert resp.status_code == 404

    def test_create_score_too_low(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_assessment(
            client, vendor_id,
            data_handling_score=0,
        )
        assert resp.status_code == 422

    def test_create_score_too_high(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_assessment(
            client, vendor_id,
            data_handling_score=6,
        )
        assert resp.status_code == 422

    def test_create_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = _create_assessment(client, "any")
        assert resp.status_code == 403


class TestListAssessments:
    def test_list_assessments(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        _create_assessment(client, vendor_id)
        _create_assessment(
            client, vendor_id,
            assessment_date="2026-01-15",
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments",
        )

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2
        assert resp.json()["meta"]["total"] == 2

    def test_list_assessments_pagination(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        for i in range(3):
            _create_assessment(
                client, vendor_id,
                assessment_date=f"2026-01-{10 + i:02d}",
            )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments",
            params={"page": 1, "page_size": 2},
        )

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2
        assert resp.json()["meta"]["total"] == 3

    def test_list_technician_allowed(
        self, client, auth_as, admin_user, technician_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        _create_assessment(client, vendor_id)

        auth_as(technician_user)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments",
        )
        assert resp.status_code == 200

    def test_list_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get(
            "/api/v1/vendors/any/assessments",
        )
        assert resp.status_code == 403


class TestGetAssessment:
    def test_get_assessment(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = _create_assessment(client, vendor_id)
        assessment_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments/{assessment_id}",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == assessment_id
        assert data["overall_risk_level"] == "medium"

    def test_get_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments/nonexistent",
        )
        assert resp.status_code == 404


class TestDeleteAssessment:
    def test_delete_assessment(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = _create_assessment(client, vendor_id)
        assessment_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/assessments/{assessment_id}",
        )

        assert resp.status_code == 204

        get_resp = client.get(
            f"/api/v1/vendors/{vendor_id}/assessments/{assessment_id}",
        )
        assert get_resp.status_code == 404

    def test_delete_recalculates_vendor_risk_level(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        # First assessment: low risk
        _create_assessment(
            client, vendor_id,
            assessment_date="2026-01-01",
            data_handling_score=1,
            security_certs_score=1,
            incident_response_score=1,
            business_continuity_score=1,
            subcontractor_score=1,
        )

        # Second assessment: high risk (becomes latest)
        resp2 = _create_assessment(
            client, vendor_id,
            assessment_date="2026-02-01",
            data_handling_score=4,
            security_certs_score=4,
            incident_response_score=4,
            business_continuity_score=4,
            subcontractor_score=4,
        )
        assessment_id = resp2.json()["data"]["id"]

        vendor_resp = client.get(f"/api/v1/vendors/{vendor_id}")
        assert vendor_resp.json()["data"]["risk_level"] == "high"

        # Delete the high-risk assessment
        client.delete(
            f"/api/v1/vendors/{vendor_id}/assessments/{assessment_id}",
        )

        # Vendor risk should recalculate to low
        vendor_resp = client.get(f"/api/v1/vendors/{vendor_id}")
        assert vendor_resp.json()["data"]["risk_level"] == "low"

    def test_delete_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/assessments/nonexistent",
        )
        assert resp.status_code == 404

    def test_delete_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.delete(
            "/api/v1/vendors/any/assessments/any",
        )
        assert resp.status_code == 403
