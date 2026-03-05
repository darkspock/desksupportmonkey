from unittest.mock import MagicMock, call

import pytest

from src.auth_bc.company_user.domain.entities import (
    CompanyUser,
    MembershipDeactivatedError,
    MembershipNotAllowedError,
)
from src.auth_bc.company_user.domain.membership_auth_service import (
    MembershipAuthService,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_user(user_id="u1", company_id="c1"):
    user = User.create(email="test@example.com", role=UserRole.EMPLOYEE, company_id=company_id)
    user.id = user_id
    return user


def _make_membership(user_id="u1", company_id="c1", role=UserRole.ADMIN, is_active=True):
    cu = CompanyUser.create(user_id=user_id, company_id=company_id, role=role)
    cu.department_id = "dept1"
    cu.employee_role_id = "er1"
    if not is_active:
        cu.deactivate()
    return cu


class TestMembershipAuthService:
    def setup_method(self):
        self.company_user_repo = MagicMock()
        self.company_lookup = MagicMock()
        self.user_repo = MagicMock()
        self.service = MembershipAuthService(
            company_user_repo=self.company_user_repo,
            company_lookup=self.company_lookup,
            user_repo=self.user_repo,
        )

    def test_path1_active_membership_copies_data(self):
        """Existing active membership → copies data to user row, returns user."""
        user = _make_user()
        membership = _make_membership()
        self.company_user_repo.find_by_user_and_company.return_value = membership

        result = self.service.resolve_membership(user, "c1", "domain")

        assert result.company_id == "c1"
        assert result.role == UserRole.ADMIN
        assert result.department_id == "dept1"
        assert result.employee_role_id == "er1"
        self.user_repo.save.assert_called_once_with(user)

    def test_path2_inactive_membership_raises(self):
        """Existing inactive membership → raises MembershipDeactivatedError."""
        user = _make_user()
        membership = _make_membership(is_active=False)
        self.company_user_repo.find_by_user_and_company.return_value = membership

        with pytest.raises(MembershipDeactivatedError):
            self.service.resolve_membership(user, "c1", "domain")

        self.user_repo.save.assert_not_called()

    def test_path3_no_membership_domain_mode_email_allowed(self):
        """No membership + domain mode + email allowed → auto-creates, copies, returns."""
        user = _make_user()
        self.company_user_repo.find_by_user_and_company.return_value = None
        self.company_lookup.is_email_allowed_in_company.return_value = True

        result = self.service.resolve_membership(user, "c1", "domain")

        # Should auto-create membership
        self.company_user_repo.save.assert_called_once()
        saved_membership = self.company_user_repo.save.call_args[0][0]
        assert isinstance(saved_membership, CompanyUser)
        assert saved_membership.user_id == "u1"
        assert saved_membership.company_id == "c1"
        assert saved_membership.role == UserRole.EMPLOYEE

        # Should copy membership to user
        assert result.company_id == "c1"
        assert result.role == UserRole.EMPLOYEE
        self.user_repo.save.assert_called_once_with(user)

    def test_path4_no_membership_domain_mode_email_not_allowed(self):
        """No membership + domain mode + email NOT allowed → raises MembershipNotAllowedError."""
        user = _make_user()
        self.company_user_repo.find_by_user_and_company.return_value = None
        self.company_lookup.is_email_allowed_in_company.return_value = False

        with pytest.raises(MembershipNotAllowedError):
            self.service.resolve_membership(user, "c1", "domain")

        self.company_user_repo.save.assert_not_called()
        self.user_repo.save.assert_not_called()

    def test_path5_no_membership_membership_only_mode(self):
        """No membership + membership_only mode → raises MembershipNotAllowedError."""
        user = _make_user()
        self.company_user_repo.find_by_user_and_company.return_value = None

        with pytest.raises(MembershipNotAllowedError):
            self.service.resolve_membership(user, "c1", "membership_only")

        # Should NOT check email domain in membership_only mode
        self.company_lookup.is_email_allowed_in_company.assert_not_called()
        self.company_user_repo.save.assert_not_called()

    def test_copy_membership_sets_all_fields(self):
        """_copy_membership_to_user sets all required fields on user."""
        user = _make_user()
        membership = CompanyUser.create(
            user_id="u1", company_id="c2", role=UserRole.TECHNICIAN,
            department_id="d99", employee_role_id="er99",
        )
        self.company_user_repo.find_by_user_and_company.return_value = membership

        result = self.service.resolve_membership(user, "c2", "domain")

        assert result.company_id == "c2"
        assert result.role == UserRole.TECHNICIAN
        assert result.department_id == "d99"
        assert result.employee_role_id == "er99"
        assert result.is_active is True
