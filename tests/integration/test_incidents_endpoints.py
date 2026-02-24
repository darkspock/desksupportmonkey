"""Integration tests for /api/v1/incidents endpoints."""


def _create_incident(client, **overrides):
    payload = {
        "title": "Phishing campaign detected",
        "description": "Multiple employees received phishing emails",
        "incident_type": "phishing",
        "severity": "P2",
        "detected_at": "2026-01-15T12:00:00Z",
    }
    payload.update(overrides)
    return client.post("/api/v1/incidents", json=payload)


class TestIncidentCRUD:
    def test_create_and_get(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_incident(client)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "Phishing campaign detected"
        assert data["incident_type"] == "phishing"
        assert data["severity"] == "P2"
        assert data["status"] == "detected"
        assert data["reported_by"] == technician_user.id
        incident_id = data["id"]

        get_resp = client.get(f"/api/v1/incidents/{incident_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == incident_id
        assert len(get_resp.json()["data"]["timeline"]) >= 1

    def test_create_with_optional_fields(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_incident(
            client,
            attack_vector="SQL injection",
            data_breach_scope="5000 records",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["attack_vector"] == "SQL injection"
        assert data["data_breach_scope"] == "5000 records"

    def test_create_invalid_type(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_incident(client, incident_type="nonexistent")
        assert resp.status_code == 422

    def test_list_incidents(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_incident(client)
        _create_incident(client, title="Malware found", incident_type="malware")

        resp = client.get("/api/v1/incidents")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 2

    def test_list_filter_by_severity(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_incident(client, severity="P1")
        _create_incident(client, severity="P4")

        resp = client.get("/api/v1/incidents?severity=P1")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["severity"] == "P1"

    def test_list_filter_by_status(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_incident(client)

        resp = client.get("/api/v1/incidents?status=detected")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["status"] == "detected"

    def test_update_incident(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/incidents/{incident_id}",
            json={"title": "Updated title", "attack_vector": "Spear phishing"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Updated title"
        assert data["attack_vector"] == "Spear phishing"

    def test_get_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.get("/api/v1/incidents/nonexistent")
        assert resp.status_code == 404


class TestIncidentStatusTransitions:
    def test_full_lifecycle(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client, severity="P1")
        incident_id = create_resp.json()["data"]["id"]

        transitions = [
            ("triaged", None),
            ("contained", None),
            ("eradicated", None),
            ("recovered", None),
            ("closed", None),
        ]
        for new_status, close_reason in transitions:
            payload = {"status": new_status}
            if close_reason:
                payload["close_reason"] = close_reason
            resp = client.post(
                f"/api/v1/incidents/{incident_id}/status",
                json=payload,
            )
            assert resp.status_code == 200, f"Failed transition to {new_status}: {resp.json()}"
            assert resp.json()["data"]["status"] == new_status

        final = client.get(f"/api/v1/incidents/{incident_id}")
        assert final.json()["data"]["closed_at"] is not None

    def test_early_closure_requires_reason(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "closed"},
        )
        assert resp.status_code == 422

    def test_early_closure_with_reason(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "closed", "close_reason": "False positive"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "closed"
        assert data["close_reason"] == "False positive"

    def test_invalid_transition_returns_409(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "recovered"},
        )
        assert resp.status_code == 409


class TestIncidentSeverity:
    def test_change_severity(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client, severity="P3")
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/severity",
            json={"severity": "P1"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["severity"] == "P1"

    def test_invalid_severity_returns_422(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/severity",
            json={"severity": "INVALID"},
        )
        assert resp.status_code == 422


class TestIncidentAssignment:
    def test_assign(self, client, auth_as, technician_user, make_user):
        auth_as(technician_user)
        from src.auth_bc.user.domain.enums import UserRole
        tech2 = make_user(
            "tech2@testco.com",
            role=UserRole.TECHNICIAN,
            company_id=technician_user.company_id,
        )
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/assign",
            json={"user_id": tech2.id},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["assigned_to"] == tech2.id


class TestRegulatoryReports:
    def test_incident_has_3_reports_on_creation(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_incident(client)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert len(data["reports"]) == 3
        types = {r["report_type"] for r in data["reports"]}
        assert types == {"early_warning_24h", "detailed_72h", "final_30d"}

    def test_reports_have_countdown_data(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_incident(client)
        data = resp.json()["data"]
        for r in data["reports"]:
            assert r["time_remaining_seconds"] is not None
            assert r["elapsed_percentage"] is not None
            assert r["status"] == "pending"

    def test_list_reports_endpoint(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/incidents/{incident_id}/reports")
        assert resp.status_code == 200
        reports = resp.json()["data"]
        assert len(reports) == 3
        for r in reports:
            assert "time_remaining_seconds" in r
            assert "elapsed_percentage" in r

    def test_generate_requires_admin(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        report_id = create_resp.json()["data"]["reports"][0]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/reports/{report_id}/generate"
        )
        assert resp.status_code == 403

    def test_submit_requires_admin(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        report_id = create_resp.json()["data"]["reports"][0]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/reports/{report_id}/submit"
        )
        assert resp.status_code == 403

    def test_submit_ungenerated_report_fails(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        report_id = create_resp.json()["data"]["reports"][0]["id"]

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/reports/{report_id}/submit"
        )
        assert resp.status_code == 422

    def test_download_ungenerated_report_fails(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        report_id = create_resp.json()["data"]["reports"][0]["id"]

        auth_as(admin_user)
        resp = client.get(
            f"/api/v1/incidents/{incident_id}/reports/{report_id}/download"
        )
        assert resp.status_code == 422

    def test_report_not_found(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/reports/nonexistent/generate"
        )
        assert resp.status_code == 404


class TestAssetVendorLinking:
    def _create_asset(self, db_session, company_id: str) -> str:
        """Create a test asset directly in DB and return its ID."""
        import ulid
        from src.asset_bc.asset.infrastructure.models import AssetModel

        asset_id = str(ulid.new())
        asset = AssetModel(
            id=asset_id,
            company_id=company_id,
            type="laptop",
            brand="Dell",
            model="XPS 15",
            serial_number=f"SN-{asset_id[:8]}",
            status="assigned",
        )
        db_session.add(asset)
        db_session.flush()
        return asset_id

    def _create_vendor(self, db_session, company_id: str) -> str:
        """Create a test vendor directly in DB and return its ID."""
        import ulid
        from src.procurement_bc.vendor.infrastructure.models import VendorModel

        vendor_id = str(ulid.new())
        vendor = VendorModel(
            id=vendor_id,
            company_id=company_id,
            name=f"Test Vendor {vendor_id[:6]}",
            is_active=True,
        )
        db_session.add(vendor)
        db_session.flush()
        return vendor_id

    def test_link_asset(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        asset_id = self._create_asset(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id, "impact_description": "Compromised"},
        )
        assert resp.status_code == 200
        assets = resp.json()["data"]["assets"]
        assert len(assets) == 1
        assert assets[0]["asset_id"] == asset_id
        assert assets[0]["asset_name"] == "Dell XPS 15"
        assert assets[0]["impact_description"] == "Compromised"

    def test_link_asset_duplicate_returns_409(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        asset_id = self._create_asset(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id},
        )
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id},
        )
        assert resp.status_code == 409

    def test_unlink_asset(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        asset_id = self._create_asset(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id},
        )
        resp = client.delete(f"/api/v1/incidents/{incident_id}/assets/{asset_id}")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["assets"]) == 0

    def test_link_vendor(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        vendor_id = self._create_vendor(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/vendors",
            json={"vendor_id": vendor_id, "involvement_description": "Hosted the server"},
        )
        assert resp.status_code == 200
        vendors = resp.json()["data"]["vendors"]
        assert len(vendors) == 1
        assert vendors[0]["vendor_id"] == vendor_id
        assert vendors[0]["involvement_description"] == "Hosted the server"
        assert "Test Vendor" in vendors[0]["vendor_name"]

    def test_link_vendor_duplicate_returns_409(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        vendor_id = self._create_vendor(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/vendors",
            json={"vendor_id": vendor_id},
        )
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/vendors",
            json={"vendor_id": vendor_id},
        )
        assert resp.status_code == 409

    def test_unlink_vendor(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        vendor_id = self._create_vendor(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/vendors",
            json={"vendor_id": vendor_id},
        )
        resp = client.delete(f"/api/v1/incidents/{incident_id}/vendors/{vendor_id}")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["vendors"]) == 0

    def test_link_creates_timeline_entry(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        asset_id = self._create_asset(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id},
        )

        detail = client.get(f"/api/v1/incidents/{incident_id}").json()["data"]
        event_types = [e["event_type"] for e in detail["timeline"]]
        assert "asset_linked" in event_types

    def test_incident_detail_includes_enriched_data(self, client, auth_as, technician_user, db_session):
        auth_as(technician_user)
        asset_id = self._create_asset(db_session, technician_user.company_id)
        vendor_id = self._create_vendor(db_session, technician_user.company_id)

        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/incidents/{incident_id}/assets",
            json={"asset_id": asset_id},
        )
        client.post(
            f"/api/v1/incidents/{incident_id}/vendors",
            json={"vendor_id": vendor_id},
        )

        detail = client.get(f"/api/v1/incidents/{incident_id}").json()["data"]
        assert len(detail["assets"]) == 1
        assert detail["assets"][0]["asset_type"] == "laptop"
        assert len(detail["vendors"]) == 1
        assert detail["vendors"][0]["vendor_name"] is not None


class TestPostMortem:
    def _advance_to_recovered(self, client, incident_id: str):
        """Advance an incident through all statuses to recovered."""
        for status in ["triaged", "contained", "eradicated", "recovered"]:
            client.post(
                f"/api/v1/incidents/{incident_id}/status",
                json={"status": status},
            )

    def test_create_postmortem(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Phishing email bypassed spam filter",
                "lessons_learned": "Need better email filtering",
                "corrective_actions": "Upgrade spam filter, train employees",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["root_cause"] == "Phishing email bypassed spam filter"
        assert data["lessons_learned"] == "Need better email filtering"
        assert data["corrective_actions"] == "Upgrade spam filter, train employees"

    def test_create_postmortem_wrong_status_returns_422(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        # Incident is still in "detected" status

        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Test",
                "lessons_learned": "Test",
                "corrective_actions": "Test",
            },
        )
        assert resp.status_code == 422

    def test_create_postmortem_duplicate_returns_409(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "First PM",
                "lessons_learned": "Test",
                "corrective_actions": "Test",
            },
        )
        resp = client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Second PM",
                "lessons_learned": "Test",
                "corrective_actions": "Test",
            },
        )
        assert resp.status_code == 409

    def test_get_postmortem(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Root cause",
                "lessons_learned": "Lessons",
                "corrective_actions": "Actions",
            },
        )

        auth_as(technician_user)
        resp = client.get(f"/api/v1/incidents/{incident_id}/post-mortem")
        assert resp.status_code == 200
        assert resp.json()["data"]["root_cause"] == "Root cause"

    def test_get_postmortem_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/incidents/{incident_id}/post-mortem")
        assert resp.status_code == 404

    def test_update_postmortem(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Old root cause",
                "lessons_learned": "Old lessons",
                "corrective_actions": "Old actions",
            },
        )

        resp = client.put(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={"root_cause": "Updated root cause"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["root_cause"] == "Updated root cause"

    def test_postmortem_creates_timeline_entry(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Root cause",
                "lessons_learned": "Lessons",
                "corrective_actions": "Actions",
            },
        )

        auth_as(technician_user)
        detail = client.get(f"/api/v1/incidents/{incident_id}").json()["data"]
        event_types = [e["event_type"] for e in detail["timeline"]]
        assert "postmortem_created" in event_types

    def test_postmortem_in_incident_detail(self, client, auth_as, technician_user, admin_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        auth_as(admin_user)
        client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Root cause in detail",
                "lessons_learned": "Lessons",
                "corrective_actions": "Actions",
            },
        )

        auth_as(technician_user)
        detail = client.get(f"/api/v1/incidents/{incident_id}").json()["data"]
        assert detail["postmortem"] is not None
        assert detail["postmortem"]["root_cause"] == "Root cause in detail"

    def test_create_postmortem_requires_admin(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_incident(client)
        incident_id = create_resp.json()["data"]["id"]
        self._advance_to_recovered(client, incident_id)

        resp = client.post(
            f"/api/v1/incidents/{incident_id}/post-mortem",
            json={
                "root_cause": "Root cause",
                "lessons_learned": "Lessons",
                "corrective_actions": "Actions",
            },
        )
        assert resp.status_code == 403


class TestEmployeeReporting:
    def test_employee_report_incident(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/my/report-incident",
            json={
                "title": "Suspicious email received",
                "description": "Got a phishing email with a link",
                "incident_type": "phishing",
            },
        )
        assert resp.status_code == 201
        assert "id" in resp.json()["data"]

    def test_employee_list_my_incidents(self, client, auth_as, employee_user):
        auth_as(employee_user)
        # Report an incident first
        client.post(
            "/api/v1/my/report-incident",
            json={
                "title": "Phishing attempt",
                "description": "Suspicious link",
                "incident_type": "phishing",
            },
        )

        resp = client.get("/api/v1/my/incidents")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        item = data[0]
        assert "title" in item
        assert "incident_type" in item
        assert "severity" in item
        assert "status" in item
        # Should NOT contain sensitive fields
        assert "attack_vector" not in item
        assert "data_breach_scope" not in item
        assert "description" not in item
        assert "timeline" not in item

    def test_employee_report_creates_incident_with_default_severity(self, client, auth_as, employee_user, technician_user):
        auth_as(employee_user)
        client.post(
            "/api/v1/my/report-incident",
            json={
                "title": "Unauthorized access attempt",
                "description": "Someone tried to access server room",
                "incident_type": "unauthorized_access",
            },
        )

        # Technician can see the incident in the list
        auth_as(technician_user)
        resp = client.get("/api/v1/incidents")
        incidents = resp.json()["data"]
        employee_incident = [i for i in incidents if i["title"] == "Unauthorized access attempt"]
        assert len(employee_incident) == 1
        assert employee_incident[0]["severity"] == "P3"

    def test_employee_report_invalid_type_returns_422(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/my/report-incident",
            json={
                "title": "Test",
                "description": "Test",
                "incident_type": "nonexistent",
            },
        )
        assert resp.status_code == 422

    def test_technician_can_report_incident(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.post(
            "/api/v1/my/report-incident",
            json={
                "title": "Server compromise",
                "description": "Detected malware on server",
                "incident_type": "malware",
            },
        )
        assert resp.status_code == 201


class TestIncidentDashboard:
    def test_dashboard_returns_200(self, client, auth_as, technician_user):
        auth_as(technician_user)
        # Create some incidents first
        _create_incident(client, title="Incident A", incident_type="phishing")
        _create_incident(client, title="Incident B", incident_type="malware", severity="P1")

        resp = client.get("/api/v1/incidents/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_active"] == 2
        assert data["total_closed"] == 0

    def test_dashboard_active_by_severity(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_incident(client, severity="P1")
        _create_incident(client, severity="P1")
        _create_incident(client, severity="P3")

        resp = client.get("/api/v1/incidents/dashboard")
        data = resp.json()
        assert data["active_by_severity"].get("P1") == 2
        assert data["active_by_severity"].get("P3") == 1

    def test_dashboard_by_type(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_incident(client, incident_type="phishing")
        _create_incident(client, incident_type="phishing")
        _create_incident(client, incident_type="ddos")

        resp = client.get("/api/v1/incidents/dashboard")
        data = resp.json()
        assert data["by_type"].get("phishing") == 2
        assert data["by_type"].get("ddos") == 1

    def test_dashboard_recent_incidents(self, client, auth_as, technician_user):
        auth_as(technician_user)
        for i in range(3):
            _create_incident(client, title=f"Incident {i}")

        resp = client.get("/api/v1/incidents/dashboard")
        data = resp.json()
        assert len(data["recent_incidents"]) == 3
        titles = {r["title"] for r in data["recent_incidents"]}
        assert titles == {"Incident 0", "Incident 1", "Incident 2"}

    def test_dashboard_mttr_computed(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = _create_incident(client, title="Closed incident")
        inc_id = resp.json()["data"]["id"]

        # Move through statuses to closed
        for status in ["triaged", "contained", "eradicated", "recovered", "closed"]:
            payload = {"status": status}
            if status == "closed":
                payload["close_reason"] = "Resolved"
            client.post(f"/api/v1/incidents/{inc_id}/status", json=payload)

        resp = client.get("/api/v1/incidents/dashboard")
        data = resp.json()
        assert data["total_closed"] >= 1
        # MTTR should be set (even if very small since timestamps are close)
        assert data["mttr_hours"] is not None

    def test_dashboard_employee_forbidden(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.get("/api/v1/incidents/dashboard")
        assert resp.status_code == 403

    def test_dashboard_admin_allowed(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/incidents/dashboard")
        assert resp.status_code == 200


class TestIncidentAuthorization:
    def test_employee_cannot_access(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.get("/api/v1/incidents")
        assert resp.status_code == 403

    def test_employee_cannot_create(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = _create_incident(client)
        assert resp.status_code == 403
