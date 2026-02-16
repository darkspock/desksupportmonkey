from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.set_password import (
    NotAdminError,
    SetPasswordCommand,
    SetPasswordCommandHandler,
    UserNotFoundError,
    WeakPasswordError,
)


def _make_handler(user_repo, password_service=None):
    if password_service is None:
        password_service = MagicMock()
        password_service.hash_password.return_value = "bcrypt_hash"
    return SetPasswordCommandHandler(
        user_repo=user_repo,
        password_service=password_service,
    )


class TestSetPasswordCommand:
    def test_success(self):
        user = User.create(email="admin@example.com", role=UserRole.ADMIN, company_id="comp1")
        user.id = "admin1"
        repo = MagicMock()
        repo.find_by_id.return_value = user
        handler = _make_handler(repo)

        handler.handle(SetPasswordCommand(user_id="admin1", password="securepass"))

        assert user.password_hash == "bcrypt_hash"
        repo.save.assert_called_once()

    def test_super_admin_can_set_password(self):
        user = User.create(email="sa@example.com", role=UserRole.SUPER_ADMIN, company_id="comp1")
        user.id = "sa1"
        repo = MagicMock()
        repo.find_by_id.return_value = user
        handler = _make_handler(repo)

        handler.handle(SetPasswordCommand(user_id="sa1", password="securepass"))

        assert user.password_hash == "bcrypt_hash"

    def test_user_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = _make_handler(repo)

        with pytest.raises(UserNotFoundError):
            handler.handle(SetPasswordCommand(user_id="bad", password="securepass"))

    def test_non_admin_raises(self):
        user = User.create(email="emp@example.com", role=UserRole.EMPLOYEE, company_id="comp1")
        user.id = "emp1"
        repo = MagicMock()
        repo.find_by_id.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(NotAdminError):
            handler.handle(SetPasswordCommand(user_id="emp1", password="securepass"))

    def test_weak_password_raises(self):
        user = User.create(email="admin@example.com", role=UserRole.ADMIN, company_id="comp1")
        user.id = "admin1"
        repo = MagicMock()
        repo.find_by_id.return_value = user
        handler = _make_handler(repo)

        with pytest.raises(WeakPasswordError):
            handler.handle(SetPasswordCommand(user_id="admin1", password="short"))
