"""Integration tests for maintenance templates and plans endpoints."""


def _create_asset(client, serial):
    resp = client.post(
        "/api/v1/assets",
        json={
            "type": "laptop",
            "brand": "Lenovo",
            "model": "T14",
            "serial_number": serial,
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_template(client):
    return client.post(
        "/api/v1/maintenance-templates",
        json={
            "name": "Quarterly Laptop Maintenance",
            "default_priority": "HIGH",
            "recurrence_frequency": "QUARTERLY",
            "recurrence_interval": 1,
            "asset_type_filter": "laptop",
            "checklist_items": [
                {"title": "Inspect keyboard", "is_required": True},
                {"title": "Check battery", "is_required": True},
            ],
        },
    )


class TestMaintenanceTemplates:
    def test_template_crud(self, client, auth_as, admin_user):
        auth_as(admin_user)

        create_resp = _create_template(client)
        assert create_resp.status_code == 201
        template_id = create_resp.json()["data"]["id"]

        list_resp = client.get("/api/v1/maintenance-templates")
        assert list_resp.status_code == 200
        assert list_resp.json()["meta"]["total"] >= 1

        get_resp = client.get(f"/api/v1/maintenance-templates/{template_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == template_id

        update_resp = client.put(
            f"/api/v1/maintenance-templates/{template_id}",
            json={"name": "Quarterly Laptop Maintenance Updated"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["name"] == "Quarterly Laptop Maintenance Updated"

        delete_resp = client.delete(f"/api/v1/maintenance-templates/{template_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["data"]["is_active"] is False


class TestApplyTemplateAndPlans:
    def test_apply_and_plan_endpoints(self, client, auth_as, admin_user):
        auth_as(admin_user)

        asset_id = _create_asset(client, "TPL-SN001")
        template_resp = _create_template(client)
        template_id = template_resp.json()["data"]["id"]

        apply_resp = client.post(
            f"/api/v1/maintenance-templates/{template_id}/apply",
            json={"asset_ids": [asset_id]},
        )
        assert apply_resp.status_code == 200
        assert apply_resp.json()["data"]["success"] is True

        list_plans = client.get("/api/v1/maintenance-plans")
        assert list_plans.status_code == 200
        assert list_plans.json()["meta"]["total"] >= 1
        plan_id = list_plans.json()["data"][0]["id"]

        get_plan = client.get(f"/api/v1/maintenance-plans/{plan_id}")
        assert get_plan.status_code == 200
        assert get_plan.json()["data"]["id"] == plan_id

        deactivate_plan = client.delete(f"/api/v1/maintenance-plans/{plan_id}")
        assert deactivate_plan.status_code == 200
        assert deactivate_plan.json()["data"]["is_active"] is False
