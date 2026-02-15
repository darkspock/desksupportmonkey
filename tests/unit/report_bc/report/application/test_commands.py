from unittest.mock import MagicMock, patch

import pytest

from src.report_bc.report.application.commands.request_report import (
    RequestReportCommand,
    RequestReportCommandHandler,
)
from src.report_bc.report.application.queries.get_report import (
    GetReportQuery,
    GetReportQueryHandler,
    ReportNotFoundError,
)
from src.report_bc.report.application.queries.list_reports import (
    ListReportsQuery,
    ListReportsQueryHandler,
)
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus, ReportType


def _make_report(**overrides):
    defaults = dict(
        company_id="comp1",
        requested_by="user1",
        type="asset_inventory",
    )
    defaults.update(overrides)
    return Report.create(**defaults)


class TestRequestReportCommand:
    @patch("core.tasks.reports.generate_report")
    def test_creates_report_and_dispatches_task(self, mock_task):
        repo = MagicMock()
        report = _make_report()
        repo.save.return_value = report

        handler = RequestReportCommandHandler(report_repo=repo)
        result = handler.handle(
            RequestReportCommand(
                company_id="comp1",
                requested_by="user1",
                type="asset_inventory",
            )
        )

        assert result.type == ReportType.ASSET_INVENTORY
        assert result.status == ReportStatus.PENDING
        repo.save.assert_called_once()
        mock_task.delay.assert_called_once_with(report.id)

    @patch("core.tasks.reports.generate_report")
    def test_invalid_type_raises_error(self, mock_task):
        repo = MagicMock()
        handler = RequestReportCommandHandler(report_repo=repo)

        with pytest.raises(ValueError):
            handler.handle(
                RequestReportCommand(
                    company_id="comp1",
                    requested_by="user1",
                    type="bad_type",
                )
            )
        repo.save.assert_not_called()
        mock_task.delay.assert_not_called()


class TestListReportsQuery:
    def test_returns_paginated(self):
        reports = [_make_report() for _ in range(3)]
        repo = MagicMock()
        repo.find_all.return_value = (reports, 3)

        handler = ListReportsQueryHandler(report_repo=repo)
        result, total = handler.handle(
            ListReportsQuery(company_id="comp1", page=1, page_size=20)
        )

        assert len(result) == 3
        assert total == 3
        repo.find_all.assert_called_once_with(company_id="comp1", page=1, page_size=20)


class TestGetReportQuery:
    def test_returns_report(self):
        report = _make_report()
        repo = MagicMock()
        repo.find_by_id.return_value = report

        handler = GetReportQueryHandler(report_repo=repo)
        result = handler.handle(
            GetReportQuery(report_id=report.id, company_id="comp1")
        )

        assert result.id == report.id

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = GetReportQueryHandler(report_repo=repo)
        with pytest.raises(ReportNotFoundError):
            handler.handle(
                GetReportQuery(report_id="bad", company_id="comp1")
            )
