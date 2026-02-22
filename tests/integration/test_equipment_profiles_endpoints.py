"""Integration tests for /api/v1/equipment-profiles."""


def _create_employee_role(db_session, company_id, name="Engineer"):
    """Helper to create an employee role for tests."""
    from src.company_bc.employee_role.domain.entities import (
        EmployeeRole,
    )
    from src.company_bc.employee_role.infrastructure.repository import (
        EmployeeRoleRepository,
    )

    role = EmployeeRole.create(
        company_id=company_id, name=name,
    )
    EmployeeRoleRepository(db_session).save(role)
    db_session.flush()
    return role


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

        emp_role = _create_employee_role(
            db_session, company.id, "Software Engineer",
        )

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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
        assert data["employee_role_id"] == emp_role.id
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

        emp_role = _create_employee_role(
            db_session, company.id, "Sales Rep",
        )

        auth_as(admin_user)
        client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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

        emp_role = _create_employee_role(
            db_session, company.id, "Support Agent",
        )

        auth_as(admin_user)
        client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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

        emp_role = _create_employee_role(
            db_session, company.id, "Accountant",
        )

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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
        assert data["employee_role_id"] == emp_role.id
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

        emp_role = _create_employee_role(
            db_session, company.id, "HR Specialist",
        )

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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

        emp_role = _create_employee_role(
            db_session, company.id, "Paralegal",
        )

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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

        emp_role = _create_employee_role(
            db_session, company.id, "Marketing Analyst",
        )

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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


class TestBudgetCents:
    def test_create_profile_with_budget(
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
            company_id=company.id, name="BudgetDept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        emp_role = _create_employee_role(
            db_session, company.id, "Budget Analyst",
        )

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
                "items": [
                    {
                        "asset_type": "laptop",
                        "quantity": 1,
                        "budget_cents": 120000,
                    },
                    {
                        "asset_type": "monitor",
                        "quantity": 1,
                    },
                ],
            },
        )

        assert resp.status_code == 201
        items = resp.json()["data"]["items"]
        laptop_item = next(
            i for i in items if i["asset_type"] == "laptop"
        )
        monitor_item = next(
            i for i in items if i["asset_type"] == "monitor"
        )
        assert laptop_item["budget_cents"] == 120000
        assert monitor_item["budget_cents"] is None

    def test_update_profile_budget(
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
            company_id=company.id, name="BudgetUpdateDept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        emp_role = _create_employee_role(
            db_session, company.id, "Buyer",
        )

        auth_as(admin_user)
        create_resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
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
                        "asset_type": "laptop",
                        "quantity": 1,
                        "budget_cents": 150000,
                    },
                ],
            },
        )

        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert items[0]["budget_cents"] == 150000


class TestMyBudget:
    def test_my_budget_returns_items(
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
            company_id=company.id, name="MyBudgetDept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        emp_role = _create_employee_role(
            db_session, company.id, "Budget Employee",
        )

        employee = make_user(
            "budgetemp@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
            department_id=dept.id,
            employee_role_id=emp_role.id,
        )

        # Create profile as admin first
        admin = make_user(
            "budgetadmin@testco.com",
            role=UserRole.ADMIN,
            company_id=company.id,
        )
        auth_as(admin)
        client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
                "items": [
                    {
                        "asset_type": "laptop",
                        "quantity": 1,
                        "budget_cents": 120000,
                    },
                    {
                        "asset_type": "monitor",
                        "quantity": 1,
                    },
                ],
            },
        )

        # Now query as employee
        auth_as(employee)
        resp = client.get(
            "/api/v1/equipment-profiles/my-budget",
        )

        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        # Only items with budget_cents are returned
        assert len(items) == 1
        assert items[0]["asset_type"] == "laptop"
        assert items[0]["budget_cents"] == 120000

    def test_my_budget_no_profile(
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
            company_id=company.id, name="NoBudgetDept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        emp_role = _create_employee_role(
            db_session, company.id, "No Budget Role",
        )

        employee = make_user(
            "nobudget@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
            department_id=dept.id,
            employee_role_id=emp_role.id,
        )

        auth_as(employee)
        resp = client.get(
            "/api/v1/equipment-profiles/my-budget",
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []

    def test_my_budget_no_department(
        self, client, auth_as, company,
        db_session, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole

        employee = make_user(
            "nodept@testco.com",
            role=UserRole.EMPLOYEE,
            company_id=company.id,
        )

        auth_as(employee)
        resp = client.get(
            "/api/v1/equipment-profiles/my-budget",
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []


class TestEmployeeRoleProfiles:
    def test_create_profile_for_different_roles(
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
            company_id=company.id, name="ProcDept",
        )
        DepartmentRepository(db_session).save(dept)
        db_session.flush()

        emp_role = _create_employee_role(
            db_session, company.id, "Procurement Specialist",
        )

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        assert resp.status_code == 201
        assert (
            resp.json()["data"]["employee_role_id"]
            == emp_role.id
        )


class TestPermissions:
    def test_employee_cannot_create(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)

        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": "dept1",
                "employee_role_id": "role1",
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

        emp_role = _create_employee_role(
            db_session, company.id, "Managed Role",
        )

        auth_as(manager)
        resp = client.post(
            "/api/v1/equipment-profiles",
            json={
                "department_id": dept.id,
                "employee_role_id": emp_role.id,
                "items": [
                    {"asset_type": "laptop", "quantity": 1},
                ],
            },
        )

        assert resp.status_code == 201
