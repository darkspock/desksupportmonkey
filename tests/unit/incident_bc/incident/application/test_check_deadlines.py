"""Tests for the deadline escalation event factory methods."""
from datetime import datetime, timezone

from src.incident_bc.incident.application.services.incident_event_factory import (
    IncidentEventFactory,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentType,
)

NOW = datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc)


def _make_incident() -> SecurityIncident:
    return SecurityIncident.create(
        company_id="comp1",
        title="Test Incident",
        description="Test",
        incident_type=IncidentType.PHISHING,
        severity=IncidentSeverity.P2,
        detected_at=NOW,
        reported_by="user1",
        id="inc1",
    )


class TestDeadlineWarningEvent:
    def test_75_percent_creates_warning(self):
        incident = _make_incident()
        event = IncidentEventFactory.deadline_warning(
            incident, "early_warning_24h", 75
        )
        assert event.event_type == "incident.deadline_warning"
        assert "75%" in event.body
        assert event.payload["elapsed_percentage"] == 75

    def test_90_percent_creates_urgent(self):
        incident = _make_incident()
        event = IncidentEventFactory.deadline_warning(
            incident, "detailed_72h", 90
        )
        assert event.event_type == "incident.deadline_urgent"
        assert "90%" in event.body
        assert event.payload["elapsed_percentage"] == 90


class TestDeadlinePassedEvent:
    def test_creates_passed_event(self):
        incident = _make_incident()
        event = IncidentEventFactory.deadline_passed(
            incident, "final_30d"
        )
        assert event.event_type == "incident.deadline_passed"
        assert "passed" in event.body.lower()
        assert event.payload["report_type"] == "final_30d"

    def test_event_has_correct_company(self):
        incident = _make_incident()
        event = IncidentEventFactory.deadline_passed(
            incident, "early_warning_24h"
        )
        assert event.company_id == "comp1"
        assert event.actor_id == "system"
