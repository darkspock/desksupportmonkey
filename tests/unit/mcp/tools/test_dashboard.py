"""Unit tests for MCP dashboard tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.dashboard import (  # noqa: E402
    handle_dashboard_aging_alerts,
    handle_dashboard_asset_summary,
    handle_dashboard_request_summary,
    handle_dashboard_request_trend,
    handle_dashboard_resolution_time,
    handle_dashboard_sla_alerts,
    handle_dashboard_warranty_alerts,
)
from core.tenant import TenantContext  # noqa: E402


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "admin-1",
        "role": "admin",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _parse_result(result):
    assert len(result) == 1
    return json.loads(result[0].text)


_P = "adapters.mcp.tools.dashboard"


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


class TestDashboardRequestSummary:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.count_by_status.return_value = {
                "submitted": 5,
                "in_review": 2,
                "in_progress": 3,
                "resolved": 10,
            }
            repo.count_by_type.return_value = {
                "incident": 12,
                "new_equipment": 5,
                "onboarding": 3,
            }
            repo.count_by_priority.return_value = {
                "low": 4,
                "medium": 8,
                "high": 5,
                "urgent": 3,
            }

            result = await handle_dashboard_request_summary({})

        data = _parse_result(result)
        assert data["total_open"] == 10
        assert data["total_resolved"] == 10
        assert data["by_status"]["submitted"] == 5
        assert data["by_type"]["incident"] == 12
        assert data["by_priority"]["urgent"] == 3


class TestDashboardResolutionTime:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.avg_resolution_time.return_value = 24.5
            repo.avg_resolution_time_by_technician.return_value = [
                {
                    "user_id": "tech-1",
                    "email": "tech@acme.com",
                    "avg_hours": 20.0,
                },
            ]

            result = await handle_dashboard_resolution_time({})

        data = _parse_result(result)
        assert data["avg_hours"] == 24.5
        assert len(data["by_technician"]) == 1
        assert data["by_technician"][0]["avg_hours"] == 20.0

    @pytest.mark.asyncio
    async def test_with_dates(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.avg_resolution_time.return_value = 12.0
            repo.avg_resolution_time_by_technician.return_value = []

            result = await handle_dashboard_resolution_time({
                "from_date": "2024-01-01",
                "to_date": "2024-06-30",
            })

        data = _parse_result(result)
        assert data["avg_hours"] == 12.0


class TestDashboardRequestTrend:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.count_by_period.return_value = [
                {
                    "period": "2024-01-01",
                    "type": "incident",
                    "count": 3,
                },
                {
                    "period": "2024-01-01",
                    "type": "new_equipment",
                    "count": 1,
                },
                {
                    "period": "2024-01-02",
                    "type": "incident",
                    "count": 5,
                },
            ]

            result = await handle_dashboard_request_trend({
                "bucket": "day",
            })

        data = _parse_result(result)
        assert data["bucket"] == "day"
        assert len(data["data"]) == 2
        assert data["data"][0]["period"] == "2024-01-01"
        assert data["data"][0]["total"] == 4
        assert data["data"][0]["by_type"]["incident"] == 3


class TestDashboardAssetSummary:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.AssetRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.count_by_status.return_value = {
                "in_stock": 10,
                "assigned": 20,
                "in_repair": 2,
                "decommissioned": 5,
            }
            repo.count_by_type.return_value = {
                "laptop": 15,
                "monitor": 12,
                "keyboard": 10,
            }

            result = await handle_dashboard_asset_summary({})

        data = _parse_result(result)
        assert data["total"] == 37
        assert data["by_status"]["assigned"] == 20
        assert data["by_type"]["laptop"] == 15


class TestDashboardWarrantyAlerts:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.AssetRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_expiring_warranties.return_value = [
                {
                    "id": "asset-1",
                    "serial_number": "SN001",
                    "warranty_expiration": "2024-02-15",
                    "days_until_expiry": 10,
                },
            ]

            result = await handle_dashboard_warranty_alerts({})

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["id"] == "asset-1"

    @pytest.mark.asyncio
    async def test_custom_days(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.AssetRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_expiring_warranties.return_value = []

            result = await handle_dashboard_warranty_alerts(
                {"days": 90},
            )

        data = _parse_result(result)
        assert data == []
        repo.find_expiring_warranties.assert_called_once_with(
            "company-1", 90,
        )


class TestDashboardAgingAlerts:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.AssetRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_aging_assets.return_value = [
                {
                    "id": "asset-2",
                    "serial_number": "SN002",
                    "purchase_date": "2020-01-15",
                    "age_years": 4.1,
                },
            ]

            result = await handle_dashboard_aging_alerts({})

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["id"] == "asset-2"


class TestDashboardSlaAlerts:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        with patch(
            f"{_P}.RequestRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_open_requests_with_age.return_value = [
                {
                    "id": "req-1",
                    "title": "Broken laptop",
                    "type": "incident",
                    "priority": "urgent",
                    "status": "submitted",
                    "assigned_to": None,
                    "created_at": datetime(2024, 1, 1, 10, 0, 0),
                    "hours_open": 10.0,
                },
            ]

            result = await handle_dashboard_sla_alerts({})

        data = _parse_result(result)
        assert len(data) == 1
        assert data[0]["id"] == "req-1"
        assert data[0]["sla_threshold_hours"] == 4
        assert data[0]["breached"] is True
