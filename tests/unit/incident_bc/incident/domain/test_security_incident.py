from datetime import datetime, timezone

import pytest

from src.incident_bc.incident.domain.entities import (
    IncidentTimeline,
    SecurityIncident,
)
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    TimelineEventType,
)
from src.incident_bc.incident.domain.exceptions import (
    CloseReasonRequiredError,
    IncidentClosedError,
    InvalidStatusTransitionError,
)


NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_incident(
    status: IncidentStatus = IncidentStatus.DETECTED,
    severity: IncidentSeverity = IncidentSeverity.P2,
) -> SecurityIncident:
    incident = SecurityIncident.create(
        company_id="comp1",
        title="Phishing campaign",
        description="Employees received phishing emails",
        incident_type=IncidentType.PHISHING,
        severity=severity,
        detected_at=NOW,
        reported_by="user1",
    )
    incident.status = status
    return incident


# --- Create ---


class TestSecurityIncidentCreate:
    def test_create_sets_detected_status(self):
        incident = SecurityIncident.create(
            company_id="comp1",
            title="Malware detected",
            description="Trojan on workstation",
            incident_type=IncidentType.MALWARE,
            severity=IncidentSeverity.P1,
            detected_at=NOW,
            reported_by="user1",
        )
        assert incident.status == IncidentStatus.DETECTED
        assert incident.incident_type == IncidentType.MALWARE
        assert incident.severity == IncidentSeverity.P1
        assert incident.assigned_to is None
        assert incident.close_reason is None
        assert incident.closed_at is None
        assert len(incident.id) == 26

    def test_create_with_custom_id(self):
        incident = SecurityIncident.create(
            company_id="comp1",
            title="Test",
            description="Desc",
            incident_type=IncidentType.OTHER,
            severity=IncidentSeverity.P4,
            detected_at=NOW,
            reported_by="user1",
            id="custom-id",
        )
        assert incident.id == "custom-id"

    def test_create_with_optional_fields(self):
        incident = SecurityIncident.create(
            company_id="comp1",
            title="Data breach",
            description="Customer DB exposed",
            incident_type=IncidentType.DATA_BREACH,
            severity=IncidentSeverity.P1,
            detected_at=NOW,
            reported_by="user1",
            attack_vector="SQL injection",
            data_breach_scope="10000 customer records",
        )
        assert incident.attack_vector == "SQL injection"
        assert incident.data_breach_scope == "10000 customer records"

    def test_create_empty_title_raises(self):
        with pytest.raises(ValueError, match="Title is required"):
            SecurityIncident.create(
                company_id="comp1",
                title="",
                description="Desc",
                incident_type=IncidentType.OTHER,
                severity=IncidentSeverity.P4,
                detected_at=NOW,
                reported_by="user1",
            )

    def test_create_empty_description_raises(self):
        with pytest.raises(ValueError, match="Description is required"):
            SecurityIncident.create(
                company_id="comp1",
                title="Title",
                description="   ",
                incident_type=IncidentType.OTHER,
                severity=IncidentSeverity.P4,
                detected_at=NOW,
                reported_by="user1",
            )

    def test_create_strips_whitespace(self):
        incident = SecurityIncident.create(
            company_id="comp1",
            title="  Malware  ",
            description="  Trojan  ",
            incident_type=IncidentType.MALWARE,
            severity=IncidentSeverity.P2,
            detected_at=NOW,
            reported_by="user1",
        )
        assert incident.title == "Malware"
        assert incident.description == "Trojan"


# --- State machine ---


class TestSecurityIncidentChangeStatus:
    def test_detected_to_triaged(self):
        incident = _make_incident(IncidentStatus.DETECTED)
        incident.change_status(IncidentStatus.TRIAGED)
        assert incident.status == IncidentStatus.TRIAGED

    def test_triaged_to_contained(self):
        incident = _make_incident(IncidentStatus.TRIAGED)
        incident.change_status(IncidentStatus.CONTAINED)
        assert incident.status == IncidentStatus.CONTAINED

    def test_contained_to_eradicated(self):
        incident = _make_incident(IncidentStatus.CONTAINED)
        incident.change_status(IncidentStatus.ERADICATED)
        assert incident.status == IncidentStatus.ERADICATED

    def test_eradicated_to_recovered(self):
        incident = _make_incident(IncidentStatus.ERADICATED)
        incident.change_status(IncidentStatus.RECOVERED)
        assert incident.status == IncidentStatus.RECOVERED

    def test_recovered_to_closed(self):
        incident = _make_incident(IncidentStatus.RECOVERED)
        incident.change_status(IncidentStatus.CLOSED)
        assert incident.status == IncidentStatus.CLOSED
        assert incident.closed_at is not None

    def test_early_closure_requires_close_reason(self):
        incident = _make_incident(IncidentStatus.DETECTED)
        with pytest.raises(CloseReasonRequiredError):
            incident.change_status(IncidentStatus.CLOSED)

    def test_early_closure_with_close_reason(self):
        incident = _make_incident(IncidentStatus.TRIAGED)
        incident.change_status(IncidentStatus.CLOSED, close_reason="False positive")
        assert incident.status == IncidentStatus.CLOSED
        assert incident.close_reason == "False positive"
        assert incident.closed_at is not None

    def test_recovered_closure_without_reason(self):
        incident = _make_incident(IncidentStatus.RECOVERED)
        incident.change_status(IncidentStatus.CLOSED)
        assert incident.status == IncidentStatus.CLOSED
        assert incident.close_reason is None

    def test_recovered_closure_with_optional_reason(self):
        incident = _make_incident(IncidentStatus.RECOVERED)
        incident.change_status(IncidentStatus.CLOSED, close_reason="All clear")
        assert incident.close_reason == "All clear"

    def test_invalid_transition_raises(self):
        incident = _make_incident(IncidentStatus.DETECTED)
        with pytest.raises(InvalidStatusTransitionError):
            incident.change_status(IncidentStatus.RECOVERED)

    def test_closed_incident_rejects_status_change(self):
        incident = _make_incident(IncidentStatus.CLOSED)
        with pytest.raises(IncidentClosedError):
            incident.change_status(IncidentStatus.DETECTED)

    def test_skip_states_not_allowed(self):
        incident = _make_incident(IncidentStatus.DETECTED)
        with pytest.raises(InvalidStatusTransitionError):
            incident.change_status(IncidentStatus.CONTAINED)


# --- Severity ---


class TestSecurityIncidentChangeSeverity:
    def test_change_severity(self):
        incident = _make_incident(severity=IncidentSeverity.P3)
        incident.change_severity(IncidentSeverity.P1)
        assert incident.severity == IncidentSeverity.P1

    def test_change_severity_on_closed_raises(self):
        incident = _make_incident(IncidentStatus.CLOSED)
        with pytest.raises(IncidentClosedError):
            incident.change_severity(IncidentSeverity.P1)


# --- Assignment ---


class TestSecurityIncidentAssign:
    def test_assign(self):
        incident = _make_incident()
        assert incident.assigned_to is None
        incident.assign_to("tech1")
        assert incident.assigned_to == "tech1"

    def test_assign_on_closed_raises(self):
        incident = _make_incident(IncidentStatus.CLOSED)
        with pytest.raises(IncidentClosedError):
            incident.assign_to("tech1")


# --- Update details ---


class TestSecurityIncidentUpdateDetails:
    def test_update_title(self):
        incident = _make_incident()
        incident.update_details(title="New title")
        assert incident.title == "New title"

    def test_update_description(self):
        incident = _make_incident()
        incident.update_details(description="Updated desc")
        assert incident.description == "Updated desc"

    def test_update_empty_title_raises(self):
        incident = _make_incident()
        with pytest.raises(ValueError, match="Title cannot be empty"):
            incident.update_details(title="   ")

    def test_update_on_closed_raises(self):
        incident = _make_incident(IncidentStatus.CLOSED)
        with pytest.raises(IncidentClosedError):
            incident.update_details(title="New")


# --- Timeline ---


class TestIncidentTimeline:
    def test_create(self):
        entry = IncidentTimeline.create(
            incident_id="inc1",
            event_type=TimelineEventType.INCIDENT_CREATED,
            description="Incident created",
            actor_id="user1",
            metadata={"severity": "P1"},
        )
        assert len(entry.id) == 26
        assert entry.incident_id == "inc1"
        assert entry.event_type == TimelineEventType.INCIDENT_CREATED
        assert entry.description == "Incident created"
        assert entry.actor_id == "user1"
        assert entry.metadata == {"severity": "P1"}

    def test_create_without_metadata(self):
        entry = IncidentTimeline.create(
            incident_id="inc1",
            event_type=TimelineEventType.STATUS_CHANGE,
            description="Status changed",
            actor_id="user1",
        )
        assert entry.metadata is None
