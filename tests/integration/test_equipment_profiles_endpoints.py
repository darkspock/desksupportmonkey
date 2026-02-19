"""Integration tests for /api/v1/equipment-profiles."""


class TestCreateProfile:
    def test_create_profile_admin(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Engineering",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {
                        "asset_type": "laptop",
                        "quantity": 1,
                        "min_ram_gb": 16,
                    },
                ],
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["department_id"] == dept.id
        assert data["role"] == "employee"
        assert data["is_active"] is True
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_type"] == "laptop"
        assert data["items"][0]["min_ram_gb"] == 16

    def test_create_duplicate_active_profile(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Sales",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "monitor", "quantity": 1},
                ],
            },
        )

        assert resp.status_code == 409


class TestListProfiles:
    def test_list_profiles(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Support",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        resp = client.get(
            "/api/v1/equipment-profiles",
        )

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1


class TestGetProfile:
    def test_get_profile(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Finance",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "technician",
                "items": [
                    {
                        "asset_type": "laptop",
                        "quantity": 1,
                        "preferred_brand": "Dell",
                    },
                ],
            },
        )
        profile_id = create_resp.json()["data"]["id"]

        resp = client.get(
            f"/api/v1/equipment-profiles/{profile_id}",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "technician"
        assert len(data["items"]) == 1

    def test_get_not_found(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)

        resp = client.get(
            "/api/v1/equipment-profiles/nonexistent",
        )

        assert resp.status_code == 404


class TestUpdateProfile:
    def test_update_profile(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="HR",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )
        profile_id = create_resp.json()["data"]["id"]

        resp = client.put(
            f"/api/v1/equipment-profiles/{profile_id}",
            json={
                "items": [
                    {
                        "asset_type": "monitor",
                        "quantity": 2,
                    },
                    {
                        "asset_type": "keyboard",
                        "quantity": 1,
                    },
                ],
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["items"]) == 2


class TestActivateDeactivate:
    def test_deactivate_and_activate(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Legal",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )
        profile_id = create_resp.json()["data"]["id"]

        # Deactivate
        resp = client.post(
            f"/api/v1/equipment-profiles/"
            f"{profile_id}/deactivate",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

        # Re-activate
        resp = client.post(
            f"/api/v1/equipment-profiles/"
            f"{profile_id}/activate",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is True


class TestDeleteProfile:
    def test_delete_profile(
        self, client, auth_as, admin_user, company,
        db_session,
    ):
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Marketing",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )
        profile_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/equipment-profiles/{profile_id}",
        )

        assert resp.status_code == 204

        # Verify deleted
        get_resp = client.get(
            f"/api/v1/equipment-profiles/{profile_id}",
        )
        assert get_resp.status_code == 404


class TestPermissions:
    def test_employee_cannot_create(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)

        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": "dept1",
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        assert resp.status_code == 403

    def test_dept_manager_can_create(
        self, client, auth_as, company,
        db_session, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.department.domain.entities import (
            Department,
        )
        from src.company_bc.department.infrastructure.repository import (
            DepartmentRepository,
        )

        dept = Department.create(
            company_id=company.id, name="Managed",
        )
        manager = make_user(
            "deptmgr@testco.com",
            role=UserRole.TECHNICIAN,
            company_id=company.id,
        )
        dept.assign_manager(manager.id)
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        auth_as(manager)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "role": "employee",
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        assert resp.status_code == 201
