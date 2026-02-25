"""Integration tests for checklist endpoints and workflow integration."""

import pytest


TEMPLATE_WITH_CHECKLIST = {
    "name": "Incident",
    "description": "Template for checklist testing",
    "icon": "alert-circle",
    "require_all_complete": True,
    "sort_order": 0,
    "subtypes": [],
    "checklist_items": [
        {
            "title": "Required step",
            "is_required": True,
            "sort_order": 0,
        },
        {
            "title": "Optional step",
            "is_required": False,
            "sort_order": 1,
        },
    ],
}


def _create_template(client, **overrides):
    payload = {**TEMPLATE_WITH_CHECKLIST, **overrides}
    return client.post("/api/v1/workflow-templates", json=payload)


def _create_request_with_template(client, template_id, title="Test"):
    return client.post(
        "/api/v1/requests",
        json={
            "type": "incident",
            "title": title,
            "description": "Test description",
            "template_id": template_id,
        },
    )


def _advance_to_in_progress(client, request_id):
    """Advance request through submitted → in_review → in_progress."""
    client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "in_review"},
    )
    client.patch(
        f"/api/v1/requests/{request_id}/status",
        json={"status": "in_progress"},
    )


class TestChecklistAutoGeneration:
    def test_checklist_generated_on_request_create(
        self, client, auth_as, admin_user, employee_user, technician_user
    ):
        # Create template as admin
        auth_as(admin_user)
        tmpl_resp = _create_template(client)
        assert tmpl_resp.status_code == 201
        tmpl_id = tmpl_resp.json()["data"]["id"]

        # Create request as employee with template
        auth_as(employee_user)
        req_resp = _create_request_with_template(client, tmpl_id)
        assert req_resp.status_code == 201
        req_id = req_resp.json()["data"]["id"]

        # Check checklist as technician
        auth_as(technician_user)
        cl_resp = client.get(
            f"/api/v1/requests/{req_id}/checklist"
        )
        assert cl_resp.status_code == 200
        items = cl_resp.json()["data"]
        assert len(items) == 2
        assert items[0]["title"] == "Required step"
        assert items[0]["is_required"] is True
        assert items[1]["title"] == "Optional step"
        assert items[1]["is_required"] is False

        progress = cl_resp.json()["progress"]
        assert progress["total"] == 2
        assert progress["completed"] == 0
        assert progress["required_remaining"] == 1


class TestChecklistOperations:
    @pytest.fixture()
    def setup(self, client, auth_as, admin_user, employee_user,
              technician_user):
        """Create template + request + return ids."""
        auth_as(admin_user)
        tmpl_resp = _create_template(
            client, name="Repair"
        )
        tmpl_id = tmpl_resp.json()["data"]["id"]

        auth_as(employee_user)
        req_resp = _create_request_with_template(
            client, tmpl_id, title="Repair test request"
        )
        req_id = req_resp.json()["data"]["id"]

        return {
            "template_id": tmpl_id,
            "request_id": req_id,
        }

    def test_add_adhoc_item(
        self, client, auth_as, technician_user, setup
    ):
        auth_as(technician_user)
        req_id = setup["request_id"]

        resp = client.post(
            f"/api/v1/requests/{req_id}/checklist",
            json={
                "title": "Ad-hoc item",
                "is_required": False,
            },
        )

        assert resp.status_code == 201
        items = resp.json()["data"]
        titles = [i["title"] for i in items]
        assert "Ad-hoc item" in titles

    def test_toggle_item(
        self, client, auth_as, technician_user, setup
    ):
        auth_as(technician_user)
        req_id = setup["request_id"]

        # Get items
        cl = client.get(
            f"/api/v1/requests/{req_id}/checklist"
        )
        items = cl.json()["data"]
        item_id = items[0]["id"]
        assert items[0]["is_completed"] is False

        # Toggle on
        resp = client.patch(
            f"/api/v1/requests/{req_id}/checklist/{item_id}/toggle"
        )
        assert resp.status_code == 200
        toggled = next(
            i for i in resp.json()["data"] if i["id"] == item_id
        )
        assert toggled["is_completed"] is True

        # Toggle off
        resp2 = client.patch(
            f"/api/v1/requests/{req_id}/checklist/{item_id}/toggle"
        )
        toggled2 = next(
            i for i in resp2.json()["data"] if i["id"] == item_id
        )
        assert toggled2["is_completed"] is False

    def test_assign_item(
        self, client, auth_as, technician_user, setup
    ):
        auth_as(technician_user)
        req_id = setup["request_id"]

        cl = client.get(
            f"/api/v1/requests/{req_id}/checklist"
        )
        item_id = cl.json()["data"][0]["id"]

        resp = client.patch(
            f"/api/v1/requests/{req_id}/checklist/{item_id}/assign",
            json={"assignee_id": technician_user.id},
        )
        assert resp.status_code == 200
        assigned = next(
            i for i in resp.json()["data"] if i["id"] == item_id
        )
        assert assigned["assignee_id"] == technician_user.id

    def test_remove_item(
        self, client, auth_as, technician_user, setup
    ):
        auth_as(technician_user)
        req_id = setup["request_id"]

        # Add an ad-hoc item
        add_resp = client.post(
            f"/api/v1/requests/{req_id}/checklist",
            json={"title": "To remove", "is_required": False},
        )
        items = add_resp.json()["data"]
        adhoc = next(i for i in items if i["title"] == "To remove")

        # Remove it
        del_resp = client.delete(
            f"/api/v1/requests/{req_id}/checklist/{adhoc['id']}"
        )
        assert del_resp.status_code == 204

        # Verify gone
        cl = client.get(
            f"/api/v1/requests/{req_id}/checklist"
        )
        titles = [i["title"] for i in cl.json()["data"]]
        assert "To remove" not in titles


class TestResolutionGuard:
    def test_resolve_blocked_with_incomplete_required_items(
        self, client, auth_as, admin_user, employee_user,
        technician_user
    ):
        # Create template with require_all_complete
        auth_as(admin_user)
        tmpl_resp = _create_template(
            client, name="Configuration"
        )
        tmpl_id = tmpl_resp.json()["data"]["id"]

        # Create request
        auth_as(employee_user)
        req_resp = _create_request_with_template(
            client, tmpl_id, title="Guard test"
        )
        req_id = req_resp.json()["data"]["id"]

        # Advance to in_progress as technician
        auth_as(technician_user)
        _advance_to_in_progress(client, req_id)

        # Try to resolve without completing checklist
        resp = client.patch(
            f"/api/v1/requests/{req_id}/status",
            json={"status": "resolved"},
        )
        assert resp.status_code == 422
        body = resp.json()
        message = body.get("detail", "") or body.get("error", {}).get("message", "")
        assert "checklist" in message.lower()

    def test_resolve_succeeds_with_all_required_complete(
        self, client, auth_as, admin_user, employee_user,
        technician_user
    ):
        auth_as(admin_user)
        tmpl_resp = _create_template(
            client, name="Onboarding"
        )
        tmpl_id = tmpl_resp.json()["data"]["id"]

        auth_as(employee_user)
        req_resp = _create_request_with_template(
            client, tmpl_id, title="Guard pass test"
        )
        req_id = req_resp.json()["data"]["id"]

        auth_as(technician_user)
        _advance_to_in_progress(client, req_id)

        # Get checklist and complete all required items
        cl = client.get(
            f"/api/v1/requests/{req_id}/checklist"
        )
        for item in cl.json()["data"]:
            if item["is_required"]:
                client.patch(
                    f"/api/v1/requests/{req_id}/checklist/"
                    f"{item['id']}/toggle"
                )

        # Now resolve should succeed
        resp = client.patch(
            f"/api/v1/requests/{req_id}/status",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200
