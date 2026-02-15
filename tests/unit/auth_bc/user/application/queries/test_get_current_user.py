from unittest.mock import MagicMock

from src.auth_bc.user.application.queries.get_current_user import (
    GetCurrentUserQuery,
    GetCurrentUserQueryHandler,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


class TestGetCurrentUserQueryHandler:
    def setup_method(self):
        self.user_repo = MagicMock()
        self.handler = GetCurrentUserQueryHandler(user_repo=self.user_repo)

    def test_returns_active_user(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        self.user_repo.find_by_id.return_value = user

        result = self.handler.handle(GetCurrentUserQuery(user_id=user.id))
        assert result == user

    def test_returns_none_for_missing_user(self):
        self.user_repo.find_by_id.return_value = None

        result = self.handler.handle(GetCurrentUserQuery(user_id="nonexistent"))
        assert result is None

    def test_returns_none_for_inactive_user(self):
        user = User.create(email="test@example.com", role=UserRole.EMPLOYEE)
        user.deactivate()
        self.user_repo.find_by_id.return_value = user

        result = self.handler.handle(GetCurrentUserQuery(user_id=user.id))
        assert result is None
