from src.auth_bc.company_user.domain.entities import (
    CompanyUser,
    MembershipDeactivatedError,
    MembershipNotAllowedError,
    MembershipNotFoundError,
    MultipleCompaniesError,
)
from src.auth_bc.user.domain.enums import UserRole


class TestCompanyUserCreate:
    def test_create_generates_ulid(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        assert len(cu.id) == 26

    def test_create_defaults_employee_role(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        assert cu.role == UserRole.EMPLOYEE

    def test_create_defaults_is_active_true(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        assert cu.is_active is True

    def test_create_with_explicit_role(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1", role=UserRole.ADMIN)
        assert cu.role == UserRole.ADMIN

    def test_create_with_department_and_employee_role(self):
        cu = CompanyUser.create(
            user_id="u1",
            company_id="c1",
            department_id="d1",
            employee_role_id="er1",
        )
        assert cu.department_id == "d1"
        assert cu.employee_role_id == "er1"

    def test_create_defaults_none_for_optional_fields(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        assert cu.department_id is None
        assert cu.employee_role_id is None
        assert cu.created_at is None
        assert cu.updated_at is None


class TestCompanyUserBehavior:
    def test_change_role(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        cu.change_role(UserRole.TECHNICIAN)
        assert cu.role == UserRole.TECHNICIAN

    def test_deactivate(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        assert cu.is_active is True
        cu.deactivate()
        assert cu.is_active is False

    def test_activate(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        cu.deactivate()
        cu.activate()
        assert cu.is_active is True

    def test_assign_department(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        cu.assign_department("dept1")
        assert cu.department_id == "dept1"

    def test_assign_department_none(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1", department_id="dept1")
        cu.assign_department(None)
        assert cu.department_id is None

    def test_assign_employee_role(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1")
        cu.assign_employee_role("er1")
        assert cu.employee_role_id == "er1"

    def test_assign_employee_role_none(self):
        cu = CompanyUser.create(user_id="u1", company_id="c1", employee_role_id="er1")
        cu.assign_employee_role(None)
        assert cu.employee_role_id is None


class TestDomainExceptions:
    def test_multiple_companies_error_stores_slugs(self):
        slugs = ["acme-corp", "beta-inc"]
        err = MultipleCompaniesError(slugs)
        assert err.slugs == slugs
        assert "acme-corp" in str(err)
        assert "beta-inc" in str(err)

    def test_membership_not_found_error(self):
        err = MembershipNotFoundError("not found")
        assert str(err) == "not found"

    def test_membership_deactivated_error(self):
        err = MembershipDeactivatedError("deactivated")
        assert str(err) == "deactivated"

    def test_membership_not_allowed_error(self):
        err = MembershipNotAllowedError("not allowed")
        assert str(err) == "not allowed"
