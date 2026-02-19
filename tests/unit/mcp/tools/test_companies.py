"""Unit tests for MCP company tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.companies import (  # noqa: E402
    handle_change_company_status,
    handle_create_company,
    handle_get_company,
    handle_list_companies,
    handle_update_company,
)
from core.tenant import TenantContext  # noqa: E402
from src.company_bc.company.application.commands import (  # noqa: E402
    create_company as _cc,
    update_company as _uc,
)
from src.company_bc.company.application.queries import (  # noqa: E402
    get_company as _gc,
)
from src.company_bc.company.domain.entities import (  # noqa: E402
    Company,
    InvalidStatusTransitionError,
)
from src.company_bc.company.domain.enums import (  # noqa: E402
    CompanyStatus,
)

CompanyNameExistsError = _cc.CompanyNameExistsError
UpdateNotFoundError = _uc.CompanyNotFoundError
CompanyDetail = _gc.CompanyDetail
GetNotFoundError = _gc.CompanyNotFoundError


def _make_company(**overrides) -> Company:
    defaults = {
        "id": "company-1",
        "name": "Acme Corp",
        "status": CompanyStatus.ACTIVE,
        "email_domains": ["acme.com"],
        "is_active": True,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return Company(**defaults)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "superadmin-1",
        "role": "super_admin",
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
        "adapters.mcp.tools.companies.SessionLocal"
    ) as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        "adapters.mcp.tools.companies.get_tenant",
        return_value=tenant,
    ):
        yield tenant


_P = "adapters.mcp.tools.companies"


class TestCreateCompany:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        company = _make_company()

        with patch(
            f"{_P}.CreateCompanyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ) as MockRepo, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.MagicLinkRepository"
        ), patch(
            f"{_P}.get_email_service"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )
            repo = MockRepo.return_value
            repo.find_by_name.return_value = company

            result = await handle_create_company({
                "name": "Acme Corp",
                "email_domains": ["acme.com"],
            })

        data = _parse_result(result)
        assert data["name"] == "Acme Corp"
        assert data["status"] == "active"
        assert data["email_domains"] == ["acme.com"]

    @pytest.mark.asyncio
    async def test_name_exists(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.CreateCompanyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ), patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.MagicLinkRepository"
        ), patch(
            f"{_P}.get_email_service"
        ):
            MockHandler.return_value.handle.side_effect = (
                CompanyNameExistsError(
                    "Company with this name already exists"
                )
            )

            result = await handle_create_company({
                "name": "Acme Corp",
                "email_domains": ["acme.com"],
            })

        data = _parse_result(result)
        assert "error" in data
        assert "already exists" in data["error"]


class TestListCompanies:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        companies = [
            _make_company(),
            _make_company(
                id="company-2", name="Beta Inc",
            ),
        ]

        with patch(
            f"{_P}.ListCompaniesQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                companies, 2,
            )

            result = await handle_list_companies({
                "page": 1, "page_size": 20,
            })

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1


class TestGetCompany:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        company = _make_company()
        detail = CompanyDetail(
            company=company,
            user_count=10,
            department_count=3,
        )

        with patch(
            f"{_P}.GetCompanyQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                detail
            )

            result = await handle_get_company({
                "company_id": "company-1",
            })

        data = _parse_result(result)
        assert data["id"] == "company-1"
        assert data["name"] == "Acme Corp"
        assert data["user_count"] == 10
        assert data["department_count"] == 3

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetCompanyQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                GetNotFoundError("Company not found")
            )

            result = await handle_get_company({
                "company_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestUpdateCompany:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        company = _make_company(name="Acme Inc")
        detail = CompanyDetail(
            company=company,
            user_count=10,
            department_count=3,
        )

        with patch(
            f"{_P}.UpdateCompanyCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetCompanyQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.CompanyRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_update_company({
                "company_id": "company-1",
                "name": "Acme Inc",
            })

        data = _parse_result(result)
        assert data["name"] == "Acme Inc"

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.UpdateCompanyCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.CompanyRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                UpdateNotFoundError("Company not found")
            )

            result = await handle_update_company({
                "company_id": "xyz",
                "name": "New Name",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestChangeCompanyStatus:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        company = _make_company(
            status=CompanyStatus.SUSPENDED,
            is_active=False,
        )
        detail = CompanyDetail(
            company=company,
            user_count=10,
            department_count=3,
        )

        with patch(
            f"{_P}.UpdateCompanyStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetCompanyQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.CompanyRepository"
        ):
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                detail
            )

            result = await handle_change_company_status({
                "company_id": "company-1",
                "new_status": "suspended",
            })

        data = _parse_result(result)
        assert data["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_invalid_transition(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.UpdateCompanyStatusCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.CompanyRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                InvalidStatusTransitionError(
                    "Cannot transition from "
                    "'deactivated' to 'suspended'"
                )
            )

            result = await handle_change_company_status({
                "company_id": "company-1",
                "new_status": "suspended",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "transition" in data["error"].lower()
