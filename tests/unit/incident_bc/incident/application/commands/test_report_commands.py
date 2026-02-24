from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.incident_bc.incident.application.commands.generate_report import (
    GenerateReportCommand,
    GenerateReportCommandHandler,
)
from src.incident_bc.incident.application.commands.submit_report import (
    SubmitReportCommand,
    SubmitReportCommandHandler,
)
from src.incident_bc.incident.domain.entities import (
    RegulatoryReport,
    SecurityIncident,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    ReportStatus,
    ReportType,
)
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotFoundError,
    ReportNotFoundError,
    ReportNotGeneratedError,
)

NOW = datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc)


def _make_incident() -> SecurityIncident:
    return SecurityIncident.create(
        company_id="comp1",
        title="Test Incident",
        description="Test description",
        incident_type=IncidentType.PHISHING,
        severity=IncidentSeverity.P2,
        detected_at=NOW,
        reported_by="user1",
        id="inc1",
    )


def _make_report(
    status: ReportStatus = ReportStatus.PENDING,
) -> RegulatoryReport:
    return RegulatoryReport(
        id="rpt1",
        incident_id="inc1",
        report_type=ReportType.EARLY_WARNING_24H,
        status=status,
        deadline_at=NOW + timedelta(hours=24),
    )


class TestGenerateReportCommandHandler:
    @patch("core.tasks.incidents.generate_incident_report")
    def test_dispatches_celery_task(self, mock_task):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_report_by_id.return_value = _make_report()

        handler = GenerateReportCommandHandler(incident_repo=repo)
        handler.handle(
            GenerateReportCommand(
                incident_id="inc1",
                report_id="rpt1",
                company_id="comp1",
                actor_id="admin1",
            )
        )

        mock_task.delay.assert_called_once_with("rpt1", "inc1")
        repo.save_timeline.assert_called_once()

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = GenerateReportCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                GenerateReportCommand(
                    incident_id="inc1",
                    report_id="rpt1",
                    company_id="comp1",
                    actor_id="admin1",
                )
            )

    def test_raises_when_report_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_report_by_id.return_value = None

        handler = GenerateReportCommandHandler(incident_repo=repo)
        with pytest.raises(ReportNotFoundError):
            handler.handle(
                GenerateReportCommand(
                    incident_id="inc1",
                    report_id="rpt1",
                    company_id="comp1",
                    actor_id="admin1",
                )
            )

    @patch("core.tasks.incidents.generate_incident_report")
    def test_regeneration_creates_correct_timeline_event(self, mock_task):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_report_by_id.return_value = _make_report(
            status=ReportStatus.GENERATED
        )

        handler = GenerateReportCommandHandler(incident_repo=repo)
        handler.handle(
            GenerateReportCommand(
                incident_id="inc1",
                report_id="rpt1",
                company_id="comp1",
                actor_id="admin1",
            )
        )

        timeline_call = repo.save_timeline.call_args[0][0]
        assert timeline_call.event_type.value == "report_regenerated"


class TestSubmitReportCommandHandler:
    def test_submits_generated_report(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        report = _make_report(status=ReportStatus.GENERATED)
        report.file_path = "/path/to/report.pdf"
        repo.find_report_by_id.return_value = report

        handler = SubmitReportCommandHandler(incident_repo=repo)
        handler.handle(
            SubmitReportCommand(
                incident_id="inc1",
                report_id="rpt1",
                company_id="comp1",
                actor_id="admin1",
            )
        )

        repo.update_report.assert_called_once()
        repo.save_timeline.assert_called_once()
        updated_report = repo.update_report.call_args[0][0]
        assert updated_report.status == ReportStatus.SUBMITTED

    def test_raises_when_report_not_generated(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_report_by_id.return_value = _make_report(
            status=ReportStatus.PENDING
        )

        handler = SubmitReportCommandHandler(incident_repo=repo)
        with pytest.raises(ReportNotGeneratedError):
            handler.handle(
                SubmitReportCommand(
                    incident_id="inc1",
                    report_id="rpt1",
                    company_id="comp1",
                    actor_id="admin1",
                )
            )

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = SubmitReportCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                SubmitReportCommand(
                    incident_id="inc1",
                    report_id="rpt1",
                    company_id="comp1",
                    actor_id="admin1",
                )
            )

    def test_raises_when_report_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_report_by_id.return_value = None

        handler = SubmitReportCommandHandler(incident_repo=repo)
        with pytest.raises(ReportNotFoundError):
            handler.handle(
                SubmitReportCommand(
                    incident_id="inc1",
                    report_id="rpt1",
                    company_id="comp1",
                    actor_id="admin1",
                )
            )
