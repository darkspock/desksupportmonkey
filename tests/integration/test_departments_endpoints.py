"""Integration tests for /api/v1/departments endpoints (ADMIN)."""

import pytest


class TestCreateDepartment:
    def test_create_department(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/departments", json={"name": "Engineering"})

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Engineering"
        assert data["is_active"] is True

    def test_create_duplicate_department(self, client, auth_as, admin_user):
        auth_as(admin_user)
        client.post("/api/v1/departments", json={"name": "Sales"})

        resp = client.post("/api/v1/departments", json={"name": "Sales"})

        assert resp.status_code == 409


class TestListDepartments:
    def test_list_departments(self, client, auth_as, admin_user):
        auth_as(admin_user)
        client.post("/api/v1/departments", json={"name": "Dept A"})

        resp = client.get("/api/v1/departments")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    def test_list_with_pagination(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/departments?page=1&page_size=5")

        assert resp.status_code == 200
        assert resp.json()["meta"]["page_size"] == 5


class TestGetDepartment:
    def test_get_department(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/departments", json={"name": "Finance"})
        dept_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/departments/{dept_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Finance"
        assert "user_count" in data

    def test_get_department_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/departments/nonexistent")

        assert resp.status_code == 404


class TestDepartmentPriorityWeight:
    def test_update_priority_weight(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/departments", json={"name": "WeightDept"})
        dept_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/departments/{dept_id}",
            json={"name": "WeightDept", "priority_weight": 2},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["priority_weight"] == 2

    def test_list_departments_includes_priority_weight(self, client, auth_as, admin_user):
        auth_as(admin_user)
        client.post("/api/v1/departments", json={"name": "WeightDept2"})

        resp = client.get("/api/v1/departments")

        assert resp.status_code == 200
        for dept in resp.json()["data"]:
            assert "priority_weight" in dept


class TestUpdateDepartment:
    def test_update_department(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/departments", json={"name": "Old Name"})
        dept_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/departments/{dept_id}", json={"name": "New Name"})

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_update_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.put("/api/v1/departments/nonexistent", json={"name": "X"})

        assert resp.status_code == 404


class TestDeleteDepartment:
    def test_delete_department(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/departments", json={"name": "ToDelete"})
        dept_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"/api/v1/departments/{dept_id}")

        assert resp.status_code == 204

    def test_delete_department_with_users(self, client, auth_as, admin_user, db_session, company, make_user):
        """Cannot delete a department that has users assigned."""
        from src.auth_bc.user.domain.enums import UserRole

        auth_as(admin_user)
        create_resp = client.post("/api/v1/departments", json={"name": "HasUsers"})
        dept_id = create_resp.json()["data"]["id"]

        # Assign an employee to this department
        emp = make_user("deptuser@testco.com", role=UserRole.EMPLOYEE, company_id=company.id, department_id=dept_id)

        resp = client.delete(f"/api/v1/departments/{dept_id}")

        assert resp.status_code == 409

    def test_delete_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.delete("/api/v1/departments/nonexistent")

        assert resp.status_code == 404


class TestAssignManager:
    def test_assign_manager_admin_success(
        self, client, auth_as, admin_user,
        company, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/departments",
            json={"name": "WithManager"},
        )
        dept_id = resp.json()["data"]["id"]

        manager = make_user(
            "mgr@testco.com",
            role=UserRole.TECHNICIAN,
            company_id=company.id,
            name="Manager User",
        )

        resp = client.put(
            f"/api/v1/departments/{dept_id}/manager",
            json={"user_id": manager.id},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["manager_user_id"] == manager.id
        assert data["manager_email"] == "mgr@testco.com"
        assert data["manager_name"] == "Manager User"

    def test_assign_manager_forbidden_employee(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)

        resp = client.put(
            "/api/v1/departments/any-id/manager",
            json={"user_id": "u1"},
        )

        assert resp.status_code == 403


class TestRemoveManager:
    def test_remove_manager_admin_success(
        self, client, auth_as, admin_user,
        company, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/departments",
            json={"name": "RemoveMgr"},
        )
        dept_id = resp.json()["data"]["id"]

        manager = make_user(
            "mgr2@testco.com",
            role=UserRole.TECHNICIAN,
            company_id=company.id,
        )
        client.put(
            f"/api/v1/departments/{dept_id}/manager",
            json={"user_id": manager.id},
        )

        resp = client.delete(
            f"/api/v1/departments/{dept_id}/manager",
        )

        assert resp.status_code == 204

        # Verify manager was removed
        get_resp = client.get(
            f"/api/v1/departments/{dept_id}",
        )
        data = get_resp.json()["data"]
        assert data["manager_user_id"] is None


class TestDeleteDepartmentWithOpenPOs:
    def test_delete_blocked_by_open_pos(
        self, client, auth_as, admin_user,
        technician_user, db_session,
    ):
        auth_as(admin_user)
        dept_resp = client.post(
            "/api/v1/departments",
            json={"name": "POBlockedDept"},
        )
        dept_id = dept_resp.json()["data"]["id"]

        auth_as(technician_user)
        client.post(
            "/api/v1/purchase-orders",
            json={
                "vendor_name": "Vendor",
                "department_id": dept_id,
                "items": [{
                    "description": "Item",
                    "quantity": 1,
                    "unit_cost_cents": 1000,
                }],
                "request_ids": [],
            },
        )

        auth_as(admin_user)
        resp = client.delete(
            f"/api/v1/departments/{dept_id}",
        )

        assert resp.status_code == 409
        body = resp.json()
        message = body.get("error", {}).get("message", "")
        assert "purchase order" in message.lower()
