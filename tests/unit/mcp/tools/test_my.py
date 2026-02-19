"""Unit tests for MCP my tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.my import (  # noqa: E402
    handle_get_my_company_settings,
    handle_mark_all_notifications_read,
    handle_mark_notification_read,
    handle_my_equipment,
    handle_my_notifications,
    handle_my_requests,
    handle_update_my_company_settings,
)
from core.tenant import TenantContext  # noqa: E402
from src.asset_bc.asset.domain.entities import Asset  # noqa: E402
from src.asset_bc.asset.domain.enums import (  # noqa: E402
    AssetStatus,
    AssetType,
)
from src.company_bc.company.application.commands.update_company import (  # noqa: E402,E501
    DomainAlreadyTakenError,
)
from src.company_bc.company.application.queries.get_company import (  # noqa: E402,E501
    CompanyDetail,
    CompanyNotFoundError as GetCompanyNotFoundError,
)
from src.company_bc.company.domain.entities import (  # noqa: E402
    Company,
)
from src.company_bc.company.domain.enums import (  # noqa: E402
    CompanyStatus,
)
from src.notification_bc.notification.application.commands.mark_read import (  # noqa: E402,E501
    NotificationNotFoundError,
)
from src.notification_bc.notification.domain.entities import (  # noqa: E402
    Notification,
)
from src.request_bc.request.domain.entities import (  # noqa: E402
    ServiceRequest,
)
from src.request_bc.request.domain.enums import (  # noqa: E402
    RequestPriority,
    RequestStatus,
    RequestType,
)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "user-1",
        "role": "employee",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _make_asset(**overrides) -> Asset:
    defaults = {
        "id": "asset-1",
        "company_id": "company-1",
        "type": AssetType.LAPTOP,
        "brand": "Dell",
        "model": "Latitude 5520",
        "serial_number": "SN001",
        "status": AssetStatus.ASSIGNED,
        "assigned_to": "user-1",
        "department_id": None,
        "purchase_date": None,
        "warranty_expiration": None,
        "notes": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return Asset(**defaults)


def _make_request(**overrides) -> ServiceRequest:
    defaults = {
        "id": "req-1",
        "company_id": "company-1",
        "created_by": "user-1",
        "type": RequestType.INCIDENT,
        "title": "Laptop not working",
        "description": "Screen is black",
        "status": RequestStatus.SUBMITTED,
        "priority": RequestPriority.MEDIUM,
        "assigned_to": None,
        "data": None,
        "resolved_at": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return ServiceRequest(**defaults)


def _make_notification(**overrides) -> Notification:
    defaults = {
        "id": "notif-1",
        "user_id": "user-1",
        "company_id": "company-1",
        "event_type": "request_created",
        "title": "New request",
        "body": "A new request was created",
        "data": {"request_id": "req-1"},
        "is_read": False,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return Notification(**defaults)


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


def _parse_result(result):
    assert len(result) == 1
    return json.loads(result[0].text)


_P = "adapters.mcp.tools.my"


@pytest.fixture
def mock_db():
    with patch(f"{_P}.SessionLocal") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        f"{_P}.get_tenant", return_value=tenant,
    ):
        yield tenant


@pytest.fixture
def mock_admin_tenant():
    tenant = _make_tenant(role="admin")
    with patch(
        f"{_P}.get_tenant", return_value=tenant,
    ):
        yield tenant


class TestMyEquipment:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        assets = [
            _make_asset(),
            _make_asset(
                id="asset-2",
                type=AssetType.MONITOR,
                serial_number="SN002",
            ),
        ]

        with patch(
            f"{_P}.MyEquipmentQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.AssetRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                assets
            )

            result = await handle_my_equipment({})

        data = _parse_result(result)
        assert len(data) == 2
        assert data[0]["id"] == "asset-1"
        assert data[0]["type"] == "laptop"
        assert data[1]["type"] == "monitor"


class TestMyRequests:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        requests = [_make_request()]

        with patch(
            f"{_P}.MyRequestsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                requests, 1,
            )

            result = await handle_my_requests({})

        data = _parse_result(result)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Laptop not working"

    @pytest.mark.asyncio
    async def test_with_status(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.MyRequestsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.RequestRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                [], 0,
            )

            result = await handle_my_requests({
                "status": "resolved",
            })

        data = _parse_result(result)
        assert data["total"] == 0
        assert data["items"] == []


class TestMyNotifications:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        notifications = [_make_notification()]

        with patch(
            f"{_P}.ListNotificationsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.NotificationRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                notifications, 1, 1,
            )

            result = await handle_my_notifications({})

        data = _parse_result(result)
        assert data["total"] == 1
        assert data["unread_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["event_type"] == "request_created"
        assert data["items"][0]["is_read"] is False


class TestMarkNotificationRead:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.MarkReadCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.NotificationRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_mark_notification_read({
                "notification_id": "notif-1",
            })

        data = _parse_result(result)
        assert data["id"] == "notif-1"
        assert data["is_read"] is True

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.MarkReadCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.NotificationRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                NotificationNotFoundError(
                    "Notification not found"
                )
            )

            result = await handle_mark_notification_read({
                "notification_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"].lower()


class TestMarkAllNotificationsRead:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.MarkAllReadCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.NotificationRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_mark_all_notifications_read({})

        data = _parse_result(result)
        assert data["success"] is True


class TestGetMyCompanySettings:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_admin_tenant,
    ):
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

            result = await handle_get_my_company_settings({})

        data = _parse_result(result)
        assert data["id"] == "company-1"
        assert data["name"] == "Acme Corp"
        assert data["email_domains"] == ["acme.com"]

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_admin_tenant,
    ):
        with patch(
            f"{_P}.GetCompanyQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.CompanyRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                GetCompanyNotFoundError(
                    "Company not found"
                )
            )

            result = await handle_get_my_company_settings({})

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestUpdateMyCompanySettings:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_admin_tenant,
    ):
        company = _make_company(
            email_domains=["acme.com", "acme.io"],
        )
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

            result = await handle_update_my_company_settings({
                "email_domains": ["acme.com", "acme.io"],
            })

        data = _parse_result(result)
        assert data["email_domains"] == [
            "acme.com", "acme.io",
        ]

    @pytest.mark.asyncio
    async def test_domain_taken(
        self, mock_db, mock_admin_tenant,
    ):
        with patch(
            f"{_P}.UpdateCompanyCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.CompanyRepository"
        ):
            MockCmd.return_value.handle.side_effect = (
                DomainAlreadyTakenError("taken.com")
            )

            result = await handle_update_my_company_settings({
                "email_domains": ["taken.com"],
            })

        data = _parse_result(result)
        assert "error" in data
        assert "taken.com" in data["error"]
