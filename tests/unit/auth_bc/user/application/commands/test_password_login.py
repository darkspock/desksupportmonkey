from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.password_login import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordLoginRequest,
    PasswordLoginService,
)


def _make_admin(user_id="admin1", company_id="comp1", password_hash="hashed_pw"):
    user = User.create(email="admin@example.com", role=UserRole.ADMIN, company_id=company_id)
    user.id = user_id
    user.set_password_hash(password_hash)
    return user


def _make_handler(user_repo, company_lookup=None, jwt_service=None, password_service=None):
    if company_lookup is None:
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", True)
    if jwt_service is None:
        jwt_service = MagicMock()
        jwt_service.create_token.return_value = "jwt_token"
    if password_service is None:
        password_service = MagicMock()
        password_service.verify_password.return_value = True
    return PasswordLoginService(
        user_repo=user_repo,
        company_lookup=company_lookup,
        jwt_service=jwt_service,
        password_service=password_service,
    )


class TestPasswordLoginService:
    def test_success(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        token = handler.handle(PasswordLoginRequest(email="admin@example.com", password="password"))

        assert token == "jwt_token"

    def test_user_not_found_raises_invalid_credentials(self):
        repo = MagicMock()
        repo.find_by_email.return_value = None
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginRequest(email="nobody@example.com", password="password"))

    def test_non_admin_raises_invalid_credentials(self):
        user = User.create(email="emp@example.com", role=UserRole.EMPLOYEE, company_id="comp1")
        user.id = "emp1"
        user.set_password_hash("hashed")
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginRequest(email="emp@example.com", password="password"))

    def test_no_password_set_raises_invalid_credentials(self):
        user = User.create(email="admin@example.com", role=UserRole.ADMIN, company_id="comp1")
        user.id = "admin1"
        # password_hash is None
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginRequest(email="admin@example.com", password="password"))

    def test_wrong_password_raises_invalid_credentials(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        pw_svc = MagicMock()
        pw_svc.verify_password.return_value = False
        handler = _make_handler(repo, password_service=pw_svc)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginRequest(email="admin@example.com", password="wrong"))

    def test_inactive_user_raises_account_inactive(self):
        user = _make_admin()
        user.deactivate()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(AccountInactiveError):
            handler.handle(PasswordLoginRequest(email="admin@example.com", password="password"))

    def test_inactive_company_raises_account_inactive(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", False)
        handler = _make_handler(repo, company_lookup=company_lookup)

        with pytest.raises(AccountInactiveError):
            handler.handle(PasswordLoginRequest(email="admin@example.com", password="password"))


class TestPasswordLoginWithMembership:
    """Tests for password login with scoped auth (membership resolution)."""

    def test_scoped_login_resolves_membership(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user

        membership_auth = MagicMock()
        membership_auth.resolve_membership.return_value = user

        company_repo = MagicMock()
        company = MagicMock()
        company.auth_mode = MagicMock()
        company.auth_mode.value = "domain"
        company_repo.find_by_id.return_value = company

        handler = PasswordLoginService(
            user_repo=repo,
            company_lookup=MagicMock(find_company_by_email_domain=MagicMock(return_value=("comp1", True))),
            jwt_service=MagicMock(create_token=MagicMock(return_value="jwt_scoped")),
            password_service=MagicMock(verify_password=MagicMock(return_value=True)),
            membership_auth=membership_auth,
            company_repo=company_repo,
        )

        token = handler.handle(PasswordLoginRequest(
            email="admin@example.com", password="password", company_id="comp1"
        ))

        assert token == "jwt_scoped"
        membership_auth.resolve_membership.assert_called_once_with(
            user, "comp1", "domain"
        )

    def test_unscoped_login_skips_membership(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user

        membership_auth = MagicMock()
        handler = PasswordLoginService(
            user_repo=repo,
            company_lookup=MagicMock(find_company_by_email_domain=MagicMock(return_value=("comp1", True))),
            jwt_service=MagicMock(create_token=MagicMock(return_value="jwt_unscoped")),
            password_service=MagicMock(verify_password=MagicMock(return_value=True)),
            membership_auth=membership_auth,
            company_repo=MagicMock(),
        )

        token = handler.handle(PasswordLoginRequest(
            email="admin@example.com", password="password"
        ))

        assert token == "jwt_unscoped"
        membership_auth.resolve_membership.assert_not_called()

    def test_scoped_login_without_membership_service_skips(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        token = handler.handle(PasswordLoginRequest(
            email="admin@example.com", password="password", company_id="comp1"
        ))

        assert token == "jwt_token"
