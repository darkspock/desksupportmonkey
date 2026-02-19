"""Unit tests for MCP user tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.users import (  # noqa: E402
    handle_activate_user,
    handle_assign_user_department,
    handle_change_user_role,
    handle_deactivate_user,
    handle_get_user,
    handle_invite_user,
    handle_list_users,
)
from core.tenant import TenantContext  # noqa: E402
from src.auth_bc.user.application.commands import (  # noqa: E402
    activate_user as _au,
    assign_department as _ad,
    change_user_role as _cr,
    deactivate_user as _du,
)
from src.auth_bc.user.application.queries import (  # noqa: E402
    get_user_detail as _gu,
)

ActivateNotFoundError = _au.UserNotFoundError
DepartmentNotFoundError = _ad.DepartmentNotFoundError
CannotChangeSelfError = _cr.CannotChangeSelfError
CannotDeactivateSelfError = _du.CannotDeactivateSelfError
GetNotFoundError = _gu.UserNotFoundError
from src.auth_bc.user.domain.entities import User  # noqa: E402
from src.auth_bc.user.domain.enums import UserRole  # noqa: E402


def _make_user(**overrides) -> User:
    defaults = {
        "id": "user-1",
        "email": "john@acme.com",
        "name": "John Doe",
        "role": UserRole.EMPLOYEE,
        "company_id": "company-1",
        "department_id": None,
        "is_active": True,
        "password_hash": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return User(**defaults)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "admin-1",
        "role": "admin",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _parse_result(result):
    """Parse the JSON from a TextContent result list."""
    assert len(result) == 1
    return json.loads(result[0].text)


@pytest.fixture
def mock_db():
    with patch(
        "adapters.mcp.tools.users.SessionLocal"
    ) as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        "adapters.mcp.tools.users.get_tenant",
        return_value=tenant,
    ):
        yield tenant


_P = "adapters.mcp.tools.users"


class TestListUsers:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        users = [
            _make_user(),
            _make_user(
                id="user-2", email="jane@acme.com",
            ),
        ]

        with patch(
            f"{_P}.ListUsersQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                users, 2,
            )

            result = await handle_list_users({
                "page": 1, "page_size": 20,
            })

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_with_filters(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ListUsersQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                [], 0,
            )

            result = await handle_list_users({
                "role": "admin",
                "is_active": True,
            })

        data = _parse_result(result)
        assert data["total"] == 0
        assert data["items"] == []


class TestInviteUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        mock_company = MagicMock()
        mock_company.email_domains = ["acme.com"]

        with patch(
            f"{_P}.CompanyRepository"
        ) as MockCompanyRepo, patch(
            f"{_P}.UserRepository"
        ) as MockUserRepo, patch(
            f"{_P}.MagicLinkRepository"
        ), patch(
            f"{_P}.CompanyLookupService"
        ), patch(
            f"{_P}.CreateMagicLinkCommandHandler"
        ) as MockMLHandler, patch(
            f"{_P}.get_email_service"
        ):
            repo = MockCompanyRepo.return_value
            repo.find_by_id.return_value = mock_company
            user_repo = MockUserRepo.return_value
            user_repo.find_by_email.return_value = None
            MockMLHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_invite_user({
                "email": "newuser@acme.com",
            })

        data = _parse_result(result)
        assert data["success"] is True
        assert data["message"] == "Invitation sent"

    @pytest.mark.asyncio
    async def test_invalid_domain(
        self, mock_db, mock_tenant,
    ):
        mock_company = MagicMock()
        mock_company.email_domains = ["acme.com"]

        with patch(
            f"{_P}.CompanyRepository"
        ) as MockCompanyRepo, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.MagicLinkRepository"
        ):
            repo = MockCompanyRepo.return_value
            repo.find_by_id.return_value = mock_company

            result = await handle_invite_user({
                "email": "user@other.com",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "domain" in data["error"].lower()


class TestGetUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        user = _make_user()

        with patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                user
            )

            result = await handle_get_user({
                "user_id": "user-1",
            })

        data = _parse_result(result)
        assert data["id"] == "user-1"
        assert data["email"] == "john@acme.com"

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                GetNotFoundError("User not found")
            )

            result = await handle_get_user({
                "user_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestChangeUserRole:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        user = _make_user(role=UserRole.TECHNICIAN)

        with patch(
            f"{_P}.ChangeUserRoleCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.get_email_service"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                user
            )

            result = await handle_change_user_role({
                "user_id": "user-1",
                "new_role": "technician",
            })

        data = _parse_result(result)
        assert data["role"] == "technician"

    @pytest.mark.asyncio
    async def test_self_error(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ChangeUserRoleCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.get_email_service"
        ):
            MockCmd.return_value.handle.side_effect = (
                CannotChangeSelfError(
                    "Cannot change your own role"
                )
            )

            result = await handle_change_user_role({
                "user_id": "admin-1",
                "new_role": "employee",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "own role" in data["error"]


class TestActivateUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        user = _make_user(is_active=True)

        with patch(
            f"{_P}.ActivateUserCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                user
            )

            result = await handle_activate_user({
                "user_id": "user-1",
            })

        data = _parse_result(result)
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ActivateUserCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                ActivateNotFoundError("User not found")
            )

            result = await handle_activate_user({
                "user_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestDeactivateUser:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        user = _make_user(is_active=False)

        with patch(
            f"{_P}.DeactivateUserCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                user
            )

            result = await handle_deactivate_user({
                "user_id": "user-1",
            })

        data = _parse_result(result)
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_self_error(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.DeactivateUserCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.UserRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                CannotDeactivateSelfError(
                    "Cannot deactivate your own account"
                )
            )

            result = await handle_deactivate_user({
                "user_id": "admin-1",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "own account" in data["error"]


class TestAssignUserDepartment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        user = _make_user(department_id="dept-1")

        with patch(
            f"{_P}.AssignDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetUserDetailQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                user
            )

            result = await handle_assign_user_department({
                "user_id": "user-1",
                "department_id": "dept-1",
            })

        data = _parse_result(result)
        assert data["department_id"] == "dept-1"

    @pytest.mark.asyncio
    async def test_department_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AssignDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                DepartmentNotFoundError(
                    "Department not found"
                )
            )

            result = await handle_assign_user_department({
                "user_id": "user-1",
                "department_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]
