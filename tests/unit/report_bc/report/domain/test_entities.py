import pytest

from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus, ReportType


class TestReportEntity:
    def test_create_valid_report(self):
        report = Report.create(
            company_id="comp1",
            requested_by="user1",
            type="asset_inventory",
        )
        assert report.id
        assert report.company_id == "comp1"
        assert report.requested_by == "user1"
        assert report.type == ReportType.ASSET_INVENTORY

    def test_default_status_is_pending(self):
        report = Report.create(
            company_id="comp1",
            requested_by="user1",
            type="request_summary",
        )
        assert report.status == ReportStatus.PENDING

    def test_default_storage_key_is_none(self):
        report = Report.create(
            company_id="comp1",
            requested_by="user1",
            type="technician_performance",
        )
        assert report.storage_key is None
        assert report.error_message is None
        assert report.completed_at is None

    def test_invalid_type_raises_error(self):
        with pytest.raises(ValueError):
            Report.create(
                company_id="comp1",
                requested_by="user1",
                type="invalid_type",
            )

    def test_with_parameters(self):
        params = {"from_date": "2026-01-01", "to_date": "2026-01-31"}
        report = Report.create(
            company_id="comp1",
            requested_by="user1",
            type="request_summary",
            parameters=params,
        )
        assert report.parameters == params

    def test_report_type_values(self):
        assert len(ReportType) == 4
        assert ReportType.ASSET_INVENTORY.value == "asset_inventory"
        assert ReportType.REQUEST_SUMMARY.value == "request_summary"
        assert ReportType.TECHNICIAN_PERFORMANCE.value == "technician_performance"
        assert ReportType.DEPARTMENT_SPENDING.value == "department_spending"

    def test_report_status_values(self):
        assert len(ReportStatus) == 4
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.PROCESSING.value == "processing"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"
