from datetime import datetime, timedelta, timezone

import pytest

from src.incident_bc.incident.domain.entities import RegulatoryReport
from src.incident_bc.incident.domain.enums import ReportStatus, ReportType
from src.incident_bc.incident.domain.exceptions import ReportNotGeneratedError


class TestRegulatoryReportCreateForIncident:
    def test_creates_three_reports(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        assert len(reports) == 3

    def test_all_reports_are_pending(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        for r in reports:
            assert r.status == ReportStatus.PENDING

    def test_all_reports_linked_to_incident(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        for r in reports:
            assert r.incident_id == "INC001"

    def test_report_types_are_distinct(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        types = {r.report_type for r in reports}
        assert types == {
            ReportType.EARLY_WARNING_24H,
            ReportType.DETAILED_72H,
            ReportType.FINAL_30D,
        }

    def test_deadline_24h(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        early = next(r for r in reports if r.report_type == ReportType.EARLY_WARNING_24H)
        assert early.deadline_at == detected_at + timedelta(hours=24)

    def test_deadline_72h(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        detailed = next(r for r in reports if r.report_type == ReportType.DETAILED_72H)
        assert detailed.deadline_at == detected_at + timedelta(hours=72)

    def test_deadline_30d(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        final = next(r for r in reports if r.report_type == ReportType.FINAL_30D)
        assert final.deadline_at == detected_at + timedelta(days=30)

    def test_all_have_unique_ids(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        ids = {r.id for r in reports}
        assert len(ids) == 3


class TestRegulatoryReportMarkGenerated:
    def test_transitions_to_generated(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        report = reports[0]
        report.mark_generated("/path/to/report.pdf")
        assert report.status == ReportStatus.GENERATED
        assert report.file_path == "/path/to/report.pdf"
        assert report.generated_at is not None

    def test_regeneration_updates_file_path(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        report = reports[0]
        report.mark_generated("/path/v1.pdf")
        report.mark_generated("/path/v2.pdf")
        assert report.status == ReportStatus.GENERATED
        assert report.file_path == "/path/v2.pdf"


class TestRegulatoryReportMarkSubmitted:
    def test_transitions_from_generated_to_submitted(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        report = reports[0]
        report.mark_generated("/path/to/report.pdf")
        report.mark_submitted()
        assert report.status == ReportStatus.SUBMITTED
        assert report.submitted_at is not None

    def test_cannot_submit_pending_report(self):
        detected_at = datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
        reports = RegulatoryReport.create_for_incident("INC001", detected_at)
        report = reports[0]
        with pytest.raises(ReportNotGeneratedError):
            report.mark_submitted()
