"""Integration tests for /api/v1/employee-roles."""


class TestCreateEmployeeRole:
    def test_admin_can_create(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/employee-roles",
            json={
                "name": "Software Engineer",
                "description": "Builds software",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Software Engineer"
        assert data["description"] == "Builds software"
        assert data["is_active"] is True

    def test_create_without_description(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "Designer"},
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["description"] is None

    def test_duplicate_name_fails(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        client.post(
            "/api/v1/employee-roles",
            json={"name": "Duplicate Role"},
        )

        resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "Duplicate Role"},
        )

        assert resp.status_code == 409

    def test_employee_cannot_create(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "Not Allowed"},
        )

        assert resp.status_code == 403


class TestListEmployeeRoles:
    def test_list_roles(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        client.post(
            "/api/v1/employee-roles",
            json={"name": "ListRole1"},
        )
        client.post(
            "/api/v1/employee-roles",
            json={"name": "ListRole2"},
        )

        resp = client.get("/api/v1/employee-roles")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 2


class TestGetEmployeeRole:
    def test_get_role(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={
                "name": "GetMe",
                "description": "Test role",
            },
        )
        role_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/employee-roles/{role_id}",
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "GetMe"

    def test_get_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.get(
            "/api/v1/employee-roles/nonexistent",
        )

        assert resp.status_code == 404


class TestUpdateEmployeeRole:
    def test_update_role(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "OldName"},
        )
        role_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/employee-roles/{role_id}",
            json={
                "name": "NewName",
                "description": "Updated",
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "NewName"
        assert data["description"] == "Updated"


    def test_update_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/employee-roles/nonexistent",
            json={"name": "Whatever"},
        )

        assert resp.status_code == 404

    def test_update_name_conflict(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        client.post(
            "/api/v1/employee-roles",
            json={"name": "ExistingRole"},
        )
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "AnotherRole"},
        )
        role_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/employee-roles/{role_id}",
            json={"name": "ExistingRole"},
        )

        assert resp.status_code == 409

    def test_employee_cannot_update(
        self, client, auth_as, employee_user, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "NoUpdate"},
        )
        role_id = create_resp.json()["data"]["id"]

        auth_as(employee_user)
        resp = client.put(
            f"/api/v1/employee-roles/{role_id}",
            json={"name": "Hacked"},
        )

        assert resp.status_code == 403


class TestDeleteEmployeeRole:
    def test_delete_role(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "DeleteMe"},
        )
        role_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/employee-roles/{role_id}",
        )

        assert resp.status_code == 204

        # Verify deleted
        get_resp = client.get(
            f"/api/v1/employee-roles/{role_id}",
        )
        assert get_resp.status_code == 404

    def test_cannot_delete_in_use(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        """Cannot delete a role assigned to users."""
        from src.company_bc.employee_role.domain.entities import (
            EmployeeRole,
        )
        from src.company_bc.employee_role.infrastructure.repository import (  # noqa: E501
            EmployeeRoleRepository,
        )
        from src.auth_bc.user.domain.entities import User
        from src.auth_bc.user.domain.enums import UserRole
        from src.auth_bc.user.infrastructure.repository import (
            UserRepository,
        )

        # Create role directly in DB
        role = EmployeeRole.create(
            company_id=company.id,
            name="InUseRole",
        )
        EmployeeRoleRepository(db_session).save(role)
        db_session.flush()

        # Create user assigned to this role
        user = User.create(
            email="assigned@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
        )
        user.assign_employee_role(role.id)
        UserRepository(db_session).save(user)
        db_session.flush()

        auth_as(admin_user)
        resp = client.delete(
            f"/api/v1/employee-roles/{role.id}",
        )

        assert resp.status_code == 409

    def test_employee_cannot_delete(
        self, client, auth_as, employee_user, admin_user,
    ):
        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/employee-roles",
            json={"name": "NoDel"},
        )
        role_id = create_resp.json()["data"]["id"]

        auth_as(employee_user)
        resp = client.delete(
            f"/api/v1/employee-roles/{role_id}",
        )

        assert resp.status_code == 403

    def test_delete_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.delete(
            "/api/v1/employee-roles/nonexistent",
        )

        assert resp.status_code == 404
