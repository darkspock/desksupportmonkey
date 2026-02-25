"""Integration tests for /api/v1/workflow-templates endpoints."""

import pytest


TEMPLATE_PAYLOAD = {
    "name": "Test Template",
    "description": "Template for testing",
    "icon": "wrench",
    "require_all_complete": True,
    "sort_order": 0,
    "subtypes": [
        {"name": "Sub A", "description": "First subtype", "sort_order": 0},
        {"name": "Sub B", "sort_order": 1},
    ],
    "checklist_items": [
        {"title": "Step 1", "is_required": True, "sort_order": 0},
        {"title": "Step 2", "is_required": False, "sort_order": 1},
    ],
}


def _create_template(client, **overrides):
    payload = {**TEMPLATE_PAYLOAD, **overrides}
    return client.post("/api/v1/workflow-templates", json=payload)


class TestCreateTemplate:
    def test_create_as_admin(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = _create_template(client)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Test Template"
        assert data["icon"] == "wrench"
        assert data["require_all_complete"] is True
        assert len(data["subtypes"]) == 2
        assert len(data["checklist_items"]) == 2

    def test_create_as_employee_forbidden(
        self, client, auth_as, employee_user
    ):
        auth_as(employee_user)
        resp = _create_template(client)
        assert resp.status_code == 403

    def test_create_duplicate_name_fails(
        self, client, auth_as, admin_user
    ):
        auth_as(admin_user)
        _create_template(client, name="Unique Template")
        resp = _create_template(client, name="Unique Template")
        assert resp.status_code in (409, 422, 500)


class TestListTemplates:
    def test_list_templates(
        self, client, auth_as, admin_user, technician_user
    ):
        auth_as(admin_user)
        _create_template(client, name="Template A")
        _create_template(client, name="Template B")

        auth_as(technician_user)
        resp = client.get("/api/v1/workflow-templates")

        assert resp.status_code == 200
        data = resp.json()["data"]
        names = [t["name"] for t in data]
        assert "Template A" in names
        assert "Template B" in names

    def test_list_active_only(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp1 = _create_template(client, name="Active One")
        assert resp1.status_code == 201
        tmpl_id = resp1.json()["data"]["id"]

        # Deactivate it
        client.put(
            f"/api/v1/workflow-templates/{tmpl_id}",
            json={"is_active": False},
        )

        resp = client.get("/api/v1/workflow-templates?active=true")
        assert resp.status_code == 200
        ids = [t["id"] for t in resp.json()["data"]]
        assert tmpl_id not in ids


class TestGetTemplate:
    def test_get_by_id(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_template(client)
        tmpl_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/workflow-templates/{tmpl_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == tmpl_id
        assert data["name"] == "Test Template"
        assert len(data["subtypes"]) == 2
        assert len(data["checklist_items"]) == 2

    def test_get_nonexistent_returns_404(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        resp = client.get(
            "/api/v1/workflow-templates/01NONEXISTENT000000000000"
        )
        assert resp.status_code == 404


class TestUpdateTemplate:
    def test_update_name(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_template(client)
        tmpl_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/workflow-templates/{tmpl_id}",
            json={"name": "Updated Name"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Name"


class TestDeleteTemplate:
    def test_delete_template(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = _create_template(client, name="To Delete")
        tmpl_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"/api/v1/workflow-templates/{tmpl_id}")
        assert resp.status_code == 204

        # Verify gone
        get_resp = client.get(f"/api/v1/workflow-templates/{tmpl_id}")
        assert get_resp.status_code == 404

    def test_delete_template_with_linked_request_fails(
        self, client, auth_as, admin_user, employee_user
    ):
        auth_as(admin_user)
        create_resp = _create_template(client, name="Incident")
        assert create_resp.status_code == 201
        tmpl_id = create_resp.json()["data"]["id"]

        # Create a request using this template
        auth_as(employee_user)
        req_resp = client.post(
            "/api/v1/requests",
            json={
                "type": "incident",
                "title": "Test request",
                "description": "Uses template",
                "template_id": tmpl_id,
            },
        )
        assert req_resp.status_code == 201

        # Try to delete — should fail
        auth_as(admin_user)
        del_resp = client.delete(
            f"/api/v1/workflow-templates/{tmpl_id}"
        )
        assert del_resp.status_code in (409, 422)
