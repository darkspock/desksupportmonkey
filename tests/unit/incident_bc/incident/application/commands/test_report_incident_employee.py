from unittest.mock import MagicMock

from src.incident_bc.incident.application.commands.report_incident_employee import (
    ReportIncidentCommand,
    ReportIncidentCommandHandler,
)
from src.incident_bc.incident.application.queries.list_my_incidents import (
    ListMyIncidentsQuery,
    ListMyIncidentsQueryHandler,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)

from datetime import datetime, timezone


class TestReportIncidentEmployee:
    def test_report_incident_happy_path(self):
        repo = MagicMock()

        handler = ReportIncidentCommandHandler(incident_repo=repo)
        handler.handle(
            ReportIncidentCommand(
                company_id="COMP001",
                title="Suspicious email received",
                description="Got a phishing email",
                incident_type="phishing",
                reported_by="EMP001",
            )
        )

        repo.save.assert_called_once()
        incident = repo.save.call_args[0][0]
        assert incident.title == "Suspicious email received"
        assert incident.severity == IncidentSeverity.P3  # Default P3
        assert incident.status == IncidentStatus.DETECTED
        assert incident.incident_type == IncidentType.PHISHING
        assert incident.reported_by == "EMP001"

        repo.save_timeline.assert_called_once()
        timeline_entry = repo.save_timeline.call_args[0][0]
        assert timeline_entry.metadata["source"] == "employee_report"

        repo.save_reports_batch.assert_called_once()
        reports = repo.save_reports_batch.call_args[0][0]
        assert len(reports) == 3  # 3 NIS2 regulatory reports

    def test_report_incident_with_notification(self):
        repo = MagicMock()
        event_bus = MagicMock()
        db = MagicMock()

        handler = ReportIncidentCommandHandler(
            incident_repo=repo, event_bus=event_bus, db=db
        )
        handler.handle(
            ReportIncidentCommand(
                company_id="COMP001",
                title="Suspicious activity",
                description="Unauthorized access attempt",
                incident_type="unauthorized_access",
                reported_by="EMP001",
            )
        )

        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert event.event_type == "incident.employee_reported"


class TestListMyIncidents:
    def test_list_my_incidents_returns_restricted_fields(self):
        repo = MagicMock()
        repo.find_my_incidents.return_value = [
            SecurityIncident(
                id="INC001",
                company_id="COMP001",
                title="My reported incident",
                description="Sensitive details here",
                incident_type=IncidentType.PHISHING,
                severity=IncidentSeverity.P3,
                status=IncidentStatus.DETECTED,
                reported_by="EMP001",
                detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                attack_vector="email link",
                data_breach_scope="5 accounts",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ]

        handler = ListMyIncidentsQueryHandler(incident_repo=repo)
        result = handler.handle(
            ListMyIncidentsQuery(user_id="EMP001", company_id="COMP001")
        )

        assert len(result) == 1
        dto = result[0]
        assert dto.id == "INC001"
        assert dto.title == "My reported incident"
        assert dto.incident_type == "phishing"
        assert dto.severity == "P3"
        assert dto.status == "detected"
        # Sensitive fields should NOT be present in the DTO
        assert not hasattr(dto, "attack_vector")
        assert not hasattr(dto, "data_breach_scope")
        assert not hasattr(dto, "description")
        assert not hasattr(dto, "timeline")

    def test_list_my_incidents_empty(self):
        repo = MagicMock()
        repo.find_my_incidents.return_value = []

        handler = ListMyIncidentsQueryHandler(incident_repo=repo)
        result = handler.handle(
            ListMyIncidentsQuery(user_id="EMP001", company_id="COMP001")
        )

        assert result == []
