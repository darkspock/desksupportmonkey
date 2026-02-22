import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


class TestUserRole:
    def test_role_hierarchy_levels(self):
        assert UserRole.SUPER_ADMIN.level == 5
        assert UserRole.ADMIN.level == 4
        assert UserRole.PROCUREMENT_MANAGER.level == 3
        assert UserRole.TECHNICIAN.level == 2
        assert UserRole.EMPLOYEE.level == 1

    def test_has_access_higher_role(self):
        assert UserRole.SUPER_ADMIN.has_access(UserRole.ADMIN)
        assert UserRole.ADMIN.has_access(UserRole.EMPLOYEE)
        assert UserRole.PROCUREMENT_MANAGER.has_access(UserRole.TECHNICIAN)

    def test_has_access_same_role(self):
        assert UserRole.ADMIN.has_access(UserRole.ADMIN)
        assert UserRole.PROCUREMENT_MANAGER.has_access(UserRole.PROCUREMENT_MANAGER)

    def test_has_access_lower_role_denied(self):
        assert not UserRole.EMPLOYEE.has_access(UserRole.ADMIN)
        assert not UserRole.TECHNICIAN.has_access(UserRole.SUPER_ADMIN)
        assert not UserRole.TECHNICIAN.has_access(UserRole.PROCUREMENT_MANAGER)

    def test_procurement_manager_access(self):
        # procurement_manager can access technician-level resources
        assert UserRole.PROCUREMENT_MANAGER.has_access(UserRole.TECHNICIAN)
        # but cannot access admin-level resources
        assert not UserRole.PROCUREMENT_MANAGER.has_access(UserRole.ADMIN)

    def test_string_values(self):
        assert UserRole.SUPER_ADMIN.value == "super_admin"
        assert UserRole.PROCUREMENT_MANAGER.value == "procurement_manager"
        assert UserRole.EMPLOYEE.value == "employee"


class TestUser:
    def test_create_user(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        assert user.email == "test@example.com"
        assert user.role == UserRole.EMPLOYEE
        assert user.is_active is True
        assert user.company_id is None
        assert len(user.id) == 26

    def test_create_user_with_company(self):
        user = User.create(
            email="test@example.com",
            role=UserRole.ADMIN,
            company_id="01COMPANY",
            name="Test User",
        )
        assert user.company_id == "01COMPANY"
        assert user.name == "Test User"
        assert user.role == UserRole.ADMIN

    def test_create_user_normalizes_email(self):
        user = User.create(email="  TEST@Example.COM  ", role=UserRole.EMPLOYEE)
        assert user.email == "test@example.com"

    def test_create_user_invalid_email(self):
        with pytest.raises(ValueError, match="Invalid email"):
            User.create(email="not-an-email", role=UserRole.EMPLOYEE)

    def test_create_user_empty_email(self):
        with pytest.raises(ValueError, match="Invalid email"):
            User.create(email="", role=UserRole.EMPLOYEE)

    def test_deactivate(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        assert user.is_active is True
        user.deactivate()
        assert user.is_active is False

    def test_change_role(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        user.change_role(UserRole.TECHNICIAN)
        assert user.role == UserRole.TECHNICIAN

    def test_change_role_invalid(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        with pytest.raises(ValueError, match="Invalid role"):
            user.change_role("not_a_role")

    def test_activate(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        user.deactivate()
        assert user.is_active is False
        user.activate()
        assert user.is_active is True

    def test_assign_department(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        assert user.department_id is None
        user.assign_department("dept123")
        assert user.department_id == "dept123"

    def test_unassign_department(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE, department_id="dept123")
        assert user.department_id == "dept123"
        user.assign_department(None)
        assert user.department_id is None

    def test_create_with_department(self):
        user = User.create(
            email="test@example.com", role=UserRole.EMPLOYEE,
            company_id="comp1", department_id="dept1",
        )
        assert user.department_id == "dept1"
