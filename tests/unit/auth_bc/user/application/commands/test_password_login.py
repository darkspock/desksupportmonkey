from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.password_login import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordLoginCommand,
    PasswordLoginCommandHandler,
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
    return PasswordLoginCommandHandler(
        user_repo=user_repo,
        company_lookup=company_lookup,
        jwt_service=jwt_service,
        password_service=password_service,
    )


class TestPasswordLoginCommand:
    def test_success(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        token = handler.handle(PasswordLoginCommand(email="admin@example.com", password="password"))

        assert token == "jwt_token"

    def test_user_not_found_raises_invalid_credentials(self):
        repo = MagicMock()
        repo.find_by_email.return_value = None
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginCommand(email="nobody@example.com", password="password"))

    def test_non_admin_raises_invalid_credentials(self):
        user = User.create(email="emp@example.com", role=UserRole.EMPLOYEE, company_id="comp1")
        user.id = "emp1"
        user.set_password_hash("hashed")
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginCommand(email="emp@example.com", password="password"))

    def test_no_password_set_raises_invalid_credentials(self):
        user = User.create(email="admin@example.com", role=UserRole.ADMIN, company_id="comp1")
        user.id = "admin1"
        # password_hash is None
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginCommand(email="admin@example.com", password="password"))

    def test_wrong_password_raises_invalid_credentials(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        pw_svc = MagicMock()
        pw_svc.verify_password.return_value = False
        handler = _make_handler(repo, password_service=pw_svc)

        with pytest.raises(InvalidCredentialsError):
            handler.handle(PasswordLoginCommand(email="admin@example.com", password="wrong"))

    def test_inactive_user_raises_account_inactive(self):
        user = _make_admin()
        user.deactivate()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(AccountInactiveError):
            handler.handle(PasswordLoginCommand(email="admin@example.com", password="password"))

    def test_inactive_company_raises_account_inactive(self):
        user = _make_admin()
        repo = MagicMock()
        repo.find_by_email.return_value = user
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", False)
        handler = _make_handler(repo, company_lookup=company_lookup)

        with pytest.raises(AccountInactiveError):
            handler.handle(PasswordLoginCommand(email="admin@example.com", password="password"))
