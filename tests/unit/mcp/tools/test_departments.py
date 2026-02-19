"""Unit tests for MCP department tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.departments import (  # noqa: E402
    handle_create_department,
    handle_delete_department,
    handle_get_department,
    handle_list_departments,
    handle_update_department,
)
from core.tenant import TenantContext  # noqa: E402
from src.company_bc.department.application.commands import (  # noqa: E402
    create_department as _cd,
    delete_department as _dd,
    update_department as _ud,
)
from src.company_bc.department.application.queries import (  # noqa: E402
    get_department as _gd,
)
from src.company_bc.department.domain.entities import (  # noqa: E402
    Department,
)

DepartmentNameExistsError = _cd.DepartmentNameExistsError
DepartmentHasUsersError = _dd.DepartmentHasUsersError
UpdateNotFoundError = _ud.DepartmentNotFoundError
DepartmentDetail = _gd.DepartmentDetail
GetNotFoundError = _gd.DepartmentNotFoundError


def _make_department(**overrides) -> Department:
    defaults = {
        "id": "dept-1",
        "company_id": "company-1",
        "name": "Engineering",
        "is_active": True,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return Department(**defaults)


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
        "adapters.mcp.tools.departments.SessionLocal"
    ) as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        "adapters.mcp.tools.departments.get_tenant",
        return_value=tenant,
    ):
        yield tenant


_P = "adapters.mcp.tools.departments"


class TestCreateDepartment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        dept = _make_department()

        with patch(
            f"{_P}.CreateDepartmentCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.DepartmentRepository"
        ) as MockRepo:
            MockHandler.return_value.handle.return_value = (
                None
            )
            repo = MockRepo.return_value
            repo.find_by_name.return_value = dept

            result = await handle_create_department({
                "name": "Engineering",
            })

        data = _parse_result(result)
        assert data["name"] == "Engineering"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_name_exists(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.CreateDepartmentCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                DepartmentNameExistsError(
                    "Department 'Engineering' already exists"
                )
            )

            result = await handle_create_department({
                "name": "Engineering",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "already exists" in data["error"]


class TestListDepartments:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        depts = [
            _make_department(),
            _make_department(
                id="dept-2", name="Marketing",
            ),
        ]

        with patch(
            f"{_P}.ListDepartmentsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                depts, 2,
            )

            result = await handle_list_departments({
                "page": 1, "page_size": 20,
            })

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1


class TestGetDepartment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        dept = _make_department()
        detail = DepartmentDetail(
            department=dept, user_count=5,
        )

        with patch(
            f"{_P}.GetDepartmentQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                detail
            )

            result = await handle_get_department({
                "department_id": "dept-1",
            })

        data = _parse_result(result)
        assert data["id"] == "dept-1"
        assert data["name"] == "Engineering"
        assert data["user_count"] == 5

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetDepartmentQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                GetNotFoundError("Department not found")
            )

            result = await handle_get_department({
                "department_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestUpdateDepartment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        dept = _make_department(name="Eng Team")
        detail = DepartmentDetail(
            department=dept, user_count=3,
        )

        with patch(
            f"{_P}.UpdateDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetDepartmentQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_update_department({
                "department_id": "dept-1",
                "name": "Eng Team",
            })

        data = _parse_result(result)
        assert data["name"] == "Eng Team"

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.UpdateDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                UpdateNotFoundError(
                    "Department not found"
                )
            )

            result = await handle_update_department({
                "department_id": "xyz",
                "name": "New Name",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestDeleteDepartment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.DeleteDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.return_value = None

            result = await handle_delete_department({
                "department_id": "dept-1",
            })

        data = _parse_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_has_users(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.DeleteDepartmentCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.DepartmentRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                DepartmentHasUsersError(
                    "Cannot delete department with "
                    "3 assigned user(s)"
                )
            )

            result = await handle_delete_department({
                "department_id": "dept-1",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "assigned user" in data["error"]
