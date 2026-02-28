"""Integration tests for vendor dependencies + concentration risk."""


def _create_vendor(client, name="Test Vendor"):
    resp = client.post(
        "/api/v1/vendors",
        json={"name": name},
    )
    return resp.json()["data"]["id"]


def _create_dependency(client, vendor_id, **overrides):
    payload = {
        "service_description": "Cloud hosting service",
        "business_function": "cloud_infrastructure",
        "is_critical": False,
    }
    payload.update(overrides)
    return client.post(
        f"/api/v1/vendors/{vendor_id}/dependencies",
        json=payload,
    )


class TestCreateDependency:
    def test_create_dependency_admin(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_dependency(client, vendor_id)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["service_description"] == "Cloud hosting service"
        assert data["business_function"] == "cloud_infrastructure"
        assert data["is_critical"] is False

    def test_create_critical_dependency(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_dependency(
            client, vendor_id,
            is_critical=True,
            service_description="Core database",
            business_function="data_storage",
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["is_critical"] is True

    def test_create_vendor_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = _create_dependency(client, "nonexistent")
        assert resp.status_code == 404

    def test_create_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = _create_dependency(client, "any")
        assert resp.status_code == 403

    def test_create_invalid_business_function(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = _create_dependency(
            client, vendor_id,
            business_function="invalid",
        )
        assert resp.status_code == 422


class TestListDependencies:
    def test_list_dependencies(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        _create_dependency(client, vendor_id)
        _create_dependency(
            client, vendor_id,
            service_description="Another service",
        )

        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/dependencies",
        )

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2
        assert resp.json()["meta"]["total"] == 2

    def test_list_technician_allowed(
        self, client, auth_as, admin_user, technician_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        _create_dependency(client, vendor_id)

        auth_as(technician_user)
        resp = client.get(
            f"/api/v1/vendors/{vendor_id}/dependencies",
        )
        assert resp.status_code == 200

    def test_list_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get(
            "/api/v1/vendors/any/dependencies",
        )
        assert resp.status_code == 403


class TestUpdateDependency:
    def test_update_dependency(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = _create_dependency(client, vendor_id)
        dep_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/vendors/{vendor_id}/dependencies/{dep_id}",
            json={
                "service_description": "Updated service",
                "is_critical": True,
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["service_description"] == "Updated service"
        assert data["is_critical"] is True

    def test_update_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.put(
            f"/api/v1/vendors/{vendor_id}/dependencies/nonexistent",
            json={"service_description": "X"},
        )
        assert resp.status_code == 404


class TestDeleteDependency:
    def test_delete_dependency(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)
        create_resp = _create_dependency(client, vendor_id)
        dep_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/dependencies/{dep_id}",
        )
        assert resp.status_code == 204

        list_resp = client.get(
            f"/api/v1/vendors/{vendor_id}/dependencies",
        )
        assert list_resp.json()["meta"]["total"] == 0

    def test_delete_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        vendor_id = _create_vendor(client)

        resp = client.delete(
            f"/api/v1/vendors/{vendor_id}/dependencies/nonexistent",
        )
        assert resp.status_code == 404


class TestConcentrationRisk:
    def test_concentration_risk(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        v1 = _create_vendor(client, "Vendor A")
        v2 = _create_vendor(client, "Vendor B")

        # 3 critical deps for v1, 1 for v2
        for _ in range(3):
            _create_dependency(
                client, v1, is_critical=True,
                service_description="Critical service",
            )
        _create_dependency(
            client, v2, is_critical=True,
            service_description="Critical service",
        )

        resp = client.get("/api/v1/vendors/concentration-risk")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

        by_vendor = {d["vendor_id"]: d for d in data}
        assert by_vendor[v1]["percentage"] == 0.75
        assert by_vendor[v1]["is_above_threshold"] is True
        assert by_vendor[v2]["percentage"] == 0.25
        assert by_vendor[v2]["is_above_threshold"] is False

    def test_concentration_risk_no_critical(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.get("/api/v1/vendors/concentration-risk")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_concentration_risk_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get("/api/v1/vendors/concentration-risk")
        assert resp.status_code == 403
