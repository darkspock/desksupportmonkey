"""Integration tests for /api/v1/risks endpoints."""


def _create_risk(client, **overrides):
    payload = {
        "title": "Data breach via unpatched server",
        "description": "Legacy servers may be vulnerable to CVE-2025-XXXX",
        "category": "cyber",
    }
    payload.update(overrides)
    return client.post("/api/v1/risks", json=payload)


class TestRiskCRUD:
    def test_create_and_get(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = _create_risk(client)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["title"] == "Data breach via unpatched server"
        assert data["category"] == "cyber"
        assert data["status"] == "open"
        assert data["created_by"] == admin_user.id
        risk_id = data["id"]

        get_resp = client.get(f"/api/v1/risks/{risk_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == risk_id
        assert len(get_resp.json()["data"]["history"]) >= 1

    def test_create_with_owner(self, client, auth_as, admin_user, technician_user):
        auth_as(admin_user)
        resp = _create_risk(client, owner_id=technician_user.id)
        assert resp.status_code == 201
        assert resp.json()["data"]["owner_id"] == technician_user.id

    def test_create_invalid_category(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = _create_risk(client, category="nonexistent")
        assert resp.status_code == 422

    def test_list_risks(self, client, auth_as, admin_user):
        auth_as(admin_user)
        _create_risk(client)
        _create_risk(client, title="Compliance gap", category="compliance")

        resp = client.get("/api/v1/risks")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 2

    def test_list_filter_by_category(self, client, auth_as, admin_user):
        auth_as(admin_user)
        _create_risk(client, category="cyber")
        _create_risk(client, title="Op risk", category="operational")

        resp = client.get("/api/v1/risks?category=cyber")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["category"] == "cyber"

    def test_list_filter_by_status(self, client, auth_as, admin_user):
        auth_as(admin_user)
        _create_risk(client)

        resp = client.get("/api/v1/risks?status=open")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["status"] == "open"

    def test_update_risk(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        update_resp = client.put(
            f"/api/v1/risks/{risk_id}",
            json={"title": "Updated title", "category": "operational"},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()["data"]
        assert data["title"] == "Updated title"
        assert data["category"] == "operational"

    def test_delete_risk(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        del_resp = client.delete(f"/api/v1/risks/{risk_id}")
        assert del_resp.status_code == 204

        get_resp = client.get(f"/api/v1/risks/{risk_id}")
        assert get_resp.status_code == 404

    def test_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/risks/nonexistent")
        assert resp.status_code == 404


class TestRiskAssessment:
    def test_assess_risk(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        assess_resp = client.post(
            f"/api/v1/risks/{risk_id}/assess",
            json={"likelihood": 4, "impact": 5},
        )
        assert assess_resp.status_code == 200
        data = assess_resp.json()["data"]
        assert data["likelihood"] == 4
        assert data["impact"] == 5
        assert data["risk_level"] == "critical"

    def test_assess_low_risk(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        assess_resp = client.post(
            f"/api/v1/risks/{risk_id}/assess",
            json={"likelihood": 1, "impact": 1},
        )
        assert assess_resp.status_code == 200
        assert assess_resp.json()["data"]["risk_level"] == "low"

    def test_assess_records_history(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/risks/{risk_id}/assess",
            json={"likelihood": 3, "impact": 3},
        )

        history_resp = client.get(f"/api/v1/risks/{risk_id}/history")
        events = [h["event_type"] for h in history_resp.json()["data"]]
        assert "score_changed" in events

    def test_assess_invalid_scores(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/risks/{risk_id}/assess",
            json={"likelihood": 0, "impact": 3},
        )
        assert resp.status_code == 422


class TestRiskStatusAndTreatment:
    def test_change_status(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        status_resp = client.post(
            f"/api/v1/risks/{risk_id}/status",
            json={"status": "under_review"},
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["data"]["status"] == "under_review"

    def test_invalid_status_transition(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/risks/{risk_id}/status",
            json={"status": "mitigated"},
        )
        assert resp.status_code == 422

    def test_set_treatment(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        treat_resp = client.post(
            f"/api/v1/risks/{risk_id}/treatment",
            json={"treatment": "mitigate"},
        )
        assert treat_resp.status_code == 200
        assert treat_resp.json()["data"]["treatment"] == "mitigate"

    def test_get_history(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        # Create, then assess, then change status
        client.post(
            f"/api/v1/risks/{risk_id}/assess",
            json={"likelihood": 3, "impact": 3},
        )
        client.post(
            f"/api/v1/risks/{risk_id}/status",
            json={"status": "under_review"},
        )

        history_resp = client.get(f"/api/v1/risks/{risk_id}/history")
        assert history_resp.status_code == 200
        data = history_resp.json()["data"]
        assert len(data) >= 3  # created + score_changed + status_changed
        event_types = {h["event_type"] for h in data}
        assert "created" in event_types
        assert "score_changed" in event_types
        assert "status_changed" in event_types


class TestRiskMitigations:
    def test_add_mitigation(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        mit_resp = client.post(
            f"/api/v1/risks/{risk_id}/mitigations",
            json={"description": "Install firewall rules"},
        )
        assert mit_resp.status_code == 201
        data = mit_resp.json()["data"]
        assert data["description"] == "Install firewall rules"
        assert data["status"] == "open"

    def test_update_mitigation(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        mit_resp = client.post(
            f"/api/v1/risks/{risk_id}/mitigations",
            json={"description": "Patch servers"},
        )
        mit_id = mit_resp.json()["data"]["id"]

        update_resp = client.put(
            f"/api/v1/risks/{risk_id}/mitigations/{mit_id}",
            json={"status": "in_progress"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["status"] == "in_progress"

    def test_delete_mitigation(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        mit_resp = client.post(
            f"/api/v1/risks/{risk_id}/mitigations",
            json={"description": "Temp fix"},
        )
        mit_id = mit_resp.json()["data"]["id"]

        del_resp = client.delete(
            f"/api/v1/risks/{risk_id}/mitigations/{mit_id}"
        )
        assert del_resp.status_code == 204

    def test_mitigations_in_detail(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/risks/{risk_id}/mitigations",
            json={"description": "Install WAF"},
        )

        detail_resp = client.get(f"/api/v1/risks/{risk_id}")
        assert len(detail_resp.json()["data"]["mitigations"]) == 1


class TestRiskLinks:
    def test_add_link(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        link_resp = client.post(
            f"/api/v1/risks/{risk_id}/links",
            json={"link_type": "asset", "link_id": "a123"},
        )
        assert link_resp.status_code == 201
        assert link_resp.json()["data"]["link_type"] == "asset"

    def test_duplicate_link(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/risks/{risk_id}/links",
            json={"link_type": "asset", "link_id": "a123"},
        )
        dup_resp = client.post(
            f"/api/v1/risks/{risk_id}/links",
            json={"link_type": "asset", "link_id": "a123"},
        )
        assert dup_resp.status_code == 409

    def test_remove_link(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        link_resp = client.post(
            f"/api/v1/risks/{risk_id}/links",
            json={"link_type": "department", "link_id": "d123"},
        )
        link_id = link_resp.json()["data"]["id"]

        del_resp = client.delete(
            f"/api/v1/risks/{risk_id}/links/{link_id}"
        )
        assert del_resp.status_code == 204

    def test_links_in_detail(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_risk(client)
        risk_id = create_resp.json()["data"]["id"]

        client.post(
            f"/api/v1/risks/{risk_id}/links",
            json={"link_type": "vendor", "link_id": "v456"},
        )

        detail_resp = client.get(f"/api/v1/risks/{risk_id}")
        assert len(detail_resp.json()["data"]["links"]) == 1


class TestRiskAuthorization:
    def test_employee_cannot_create(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = _create_risk(client)
        assert resp.status_code == 403

    def test_technician_can_list(self, client, auth_as, admin_user, technician_user):
        auth_as(admin_user)
        _create_risk(client)

        auth_as(technician_user)
        resp = client.get("/api/v1/risks")
        assert resp.status_code == 200

    def test_technician_cannot_create(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_risk(client)
        assert resp.status_code == 403

    def test_admin_can_do_everything(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = _create_risk(client)
        assert resp.status_code == 201
