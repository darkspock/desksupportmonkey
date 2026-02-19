"""Unit tests for MCP report tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.reports import (  # noqa: E402
    handle_download_report,
    handle_get_report,
    handle_list_reports,
    handle_request_report,
)
from core.tenant import TenantContext  # noqa: E402
from src.report_bc.report.application.queries.get_report import (  # noqa: E402
    ReportNotFoundError,
)
from src.report_bc.report.domain.entities import Report  # noqa: E402
from src.report_bc.report.domain.enums import (  # noqa: E402
    ReportStatus,
    ReportType,
)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "admin-1",
        "role": "admin",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _make_report(**overrides) -> Report:
    defaults = {
        "id": "report-1",
        "company_id": "company-1",
        "requested_by": "admin-1",
        "type": ReportType.ASSET_INVENTORY,
        "status": ReportStatus.PENDING,
        "parameters": None,
        "storage_key": None,
        "error_message": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "completed_at": None,
    }
    defaults.update(overrides)
    return Report(**defaults)


def _parse_result(result):
    assert len(result) == 1
    return json.loads(result[0].text)


_P = "adapters.mcp.tools.reports"


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


class TestRequestReport:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        report = _make_report()

        with patch(
            f"{_P}.RequestReportCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.GetReportQueryHandler"
        ) as MockQuery, patch(
            f"{_P}.ReportRepository"
        ), patch(
            f"{_P}.ulid"
        ) as mock_ulid:
            mock_ulid.new.return_value = "report-1"
            MockCmd.return_value.handle.return_value = None
            MockQuery.return_value.handle.return_value = (
                report
            )

            result = await handle_request_report({
                "type": "asset_inventory",
            })

        data = _parse_result(result)
        assert data["id"] == "report-1"
        assert data["type"] == "asset_inventory"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_invalid_type(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.RequestReportCommandHandler"
        ) as MockCmd, patch(
            f"{_P}.ReportRepository"
        ), patch(
            f"{_P}.ulid"
        ) as mock_ulid:
            mock_ulid.new.return_value = "report-1"
            MockCmd.return_value.handle.side_effect = (
                ValueError("Invalid report type")
            )

            result = await handle_request_report({
                "type": "invalid_type",
            })

        data = _parse_result(result)
        assert "error" in data


class TestListReports:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        reports = [
            _make_report(),
            _make_report(
                id="report-2",
                type=ReportType.REQUEST_SUMMARY,
            ),
        ]

        with patch(
            f"{_P}.ListReportsQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.ReportRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                reports, 2,
            )

            result = await handle_list_reports({
                "page": 1, "page_size": 20,
            })

        data = _parse_result(result)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1


class TestGetReport:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        report = _make_report(
            status=ReportStatus.COMPLETED,
            completed_at=datetime(2024, 1, 15, 11, 0, 0),
        )

        with patch(
            f"{_P}.GetReportQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.ReportRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                report
            )

            result = await handle_get_report({
                "report_id": "report-1",
            })

        data = _parse_result(result)
        assert data["id"] == "report-1"
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.GetReportQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.ReportRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                ReportNotFoundError("Report not found")
            )

            result = await handle_get_report({
                "report_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestDownloadReport:
    @pytest.mark.asyncio
    async def test_success(self, mock_db, mock_tenant):
        report = _make_report(
            status=ReportStatus.COMPLETED,
            storage_key="reports/report-1.csv",
        )

        with patch(
            f"{_P}.ReportRepository"
        ) as MockRepo, patch(
            f"{_P}.S3StorageService"
        ) as MockStorage:
            MockRepo.return_value.find_by_id.return_value = (
                report
            )
            MockStorage.return_value.get_signed_url.return_value = (
                "https://s3.example.com/reports/report-1.csv?signed"
            )

            result = await handle_download_report({
                "report_id": "report-1",
            })

        data = _parse_result(result)
        assert "download_url" in data
        assert "s3.example.com" in data["download_url"]

    @pytest.mark.asyncio
    async def test_not_completed(
        self, mock_db, mock_tenant,
    ):
        report = _make_report(
            status=ReportStatus.PROCESSING,
        )

        with patch(
            f"{_P}.ReportRepository"
        ) as MockRepo:
            MockRepo.return_value.find_by_id.return_value = (
                report
            )

            result = await handle_download_report({
                "report_id": "report-1",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "processing" in data["error"]

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.ReportRepository"
        ) as MockRepo:
            MockRepo.return_value.find_by_id.return_value = (
                None
            )

            result = await handle_download_report({
                "report_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"]
