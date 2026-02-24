from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.incident_bc.incident.application.commands.assign_incident import (
    AssignIncidentCommand,
    AssignIncidentCommandHandler,
)
from src.incident_bc.incident.application.commands.change_severity import (
    ChangeIncidentSeverityCommand,
    ChangeIncidentSeverityCommandHandler,
)
from src.incident_bc.incident.application.commands.change_status import (
    ChangeIncidentStatusCommand,
    ChangeIncidentStatusCommandHandler,
)
from src.incident_bc.incident.application.commands.create_incident import (
    CreateIncidentCommand,
    CreateIncidentCommandHandler,
)
from src.incident_bc.incident.application.commands.update_incident import (
    UpdateIncidentCommand,
    UpdateIncidentCommandHandler,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from src.incident_bc.incident.domain.exceptions import (
    CloseReasonRequiredError,
    IncidentClosedError,
    IncidentNotFoundError,
    InvalidStatusTransitionError,
)

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _mock_repo():
    return MagicMock()


def _make_incident(
    status: IncidentStatus = IncidentStatus.DETECTED,
    incident_id: str = "inc1",
) -> SecurityIncident:
    i = SecurityIncident.create(
        company_id="comp1",
        title="Phishing",
        description="Phishing email campaign",
        incident_type=IncidentType.PHISHING,
        severity=IncidentSeverity.P2,
        detected_at=NOW,
        reported_by="user1",
        id=incident_id,
    )
    i.status = status
    return i


class TestCreateIncidentCommandHandler:
    def test_creates_incident_and_timeline(self):
        repo = _mock_repo()
        handler = CreateIncidentCommandHandler(incident_repo=repo)
        handler.handle(
            CreateIncidentCommand(
                company_id="comp1",
                title="Malware",
                description="Trojan found",
                incident_type="malware",
                severity="P1",
                detected_at=NOW,
                reported_by="user1",
                id="inc-test",
            )
        )
        assert repo.save.call_count == 1
        assert repo.save_timeline.call_count == 1
        saved_incident = repo.save.call_args[0][0]
        assert saved_incident.id == "inc-test"
        assert saved_incident.status == IncidentStatus.DETECTED

    def test_invalid_type_raises(self):
        repo = _mock_repo()
        handler = CreateIncidentCommandHandler(incident_repo=repo)
        with pytest.raises(ValueError):
            handler.handle(
                CreateIncidentCommand(
                    company_id="comp1",
                    title="Bad",
                    description="Bad type",
                    incident_type="nonexistent",
                    severity="P1",
                    detected_at=NOW,
                    reported_by="user1",
                )
            )

    def test_publishes_event_when_bus_present(self):
        repo = _mock_repo()
        event_bus = MagicMock()
        db = MagicMock()
        handler = CreateIncidentCommandHandler(
            incident_repo=repo, event_bus=event_bus, db=db
        )
        handler.handle(
            CreateIncidentCommand(
                company_id="comp1",
                title="DDoS",
                description="DDoS attack",
                incident_type="ddos",
                severity="P1",
                detected_at=NOW,
                reported_by="user1",
            )
        )
        event_bus.publish.assert_called_once()


class TestUpdateIncidentCommandHandler:
    def test_updates_title(self):
        repo = _mock_repo()
        incident = _make_incident()
        repo.find_by_id.return_value = incident
        handler = UpdateIncidentCommandHandler(incident_repo=repo)
        handler.handle(
            UpdateIncidentCommand(
                incident_id="inc1",
                company_id="comp1",
                actor_id="user1",
                title="Updated title",
            )
        )
        assert incident.title == "Updated title"
        repo.save.assert_called_once()
        repo.save_timeline.assert_called_once()

    def test_not_found_raises(self):
        repo = _mock_repo()
        repo.find_by_id.return_value = None
        handler = UpdateIncidentCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                UpdateIncidentCommand(
                    incident_id="bad",
                    company_id="comp1",
                    actor_id="user1",
                    title="X",
                )
            )

    def test_closed_incident_rejects(self):
        repo = _mock_repo()
        incident = _make_incident(IncidentStatus.CLOSED)
        repo.find_by_id.return_value = incident
        handler = UpdateIncidentCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentClosedError):
            handler.handle(
                UpdateIncidentCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    actor_id="user1",
                    title="X",
                )
            )


class TestChangeStatusCommandHandler:
    def test_valid_transition(self):
        repo = _mock_repo()
        incident = _make_incident(IncidentStatus.DETECTED)
        repo.find_by_id.return_value = incident
        handler = ChangeIncidentStatusCommandHandler(incident_repo=repo)
        handler.handle(
            ChangeIncidentStatusCommand(
                incident_id="inc1",
                company_id="comp1",
                new_status="triaged",
                actor_id="user1",
            )
        )
        assert incident.status == IncidentStatus.TRIAGED
        repo.save.assert_called_once()
        repo.save_timeline.assert_called_once()

    def test_invalid_transition_raises(self):
        repo = _mock_repo()
        incident = _make_incident(IncidentStatus.DETECTED)
        repo.find_by_id.return_value = incident
        handler = ChangeIncidentStatusCommandHandler(incident_repo=repo)
        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                ChangeIncidentStatusCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    new_status="recovered",
                    actor_id="user1",
                )
            )

    def test_early_closure_without_reason_raises(self):
        repo = _mock_repo()
        incident = _make_incident(IncidentStatus.DETECTED)
        repo.find_by_id.return_value = incident
        handler = ChangeIncidentStatusCommandHandler(incident_repo=repo)
        with pytest.raises(CloseReasonRequiredError):
            handler.handle(
                ChangeIncidentStatusCommand(
                    incident_id="inc1",
                    company_id="comp1",
                    new_status="closed",
                    actor_id="user1",
                )
            )

    def test_early_closure_with_reason(self):
        repo = _mock_repo()
        incident = _make_incident(IncidentStatus.TRIAGED)
        repo.find_by_id.return_value = incident
        handler = ChangeIncidentStatusCommandHandler(incident_repo=repo)
        handler.handle(
            ChangeIncidentStatusCommand(
                incident_id="inc1",
                company_id="comp1",
                new_status="closed",
                actor_id="user1",
                close_reason="False positive",
            )
        )
        assert incident.status == IncidentStatus.CLOSED
        assert incident.close_reason == "False positive"

    def test_not_found_raises(self):
        repo = _mock_repo()
        repo.find_by_id.return_value = None
        handler = ChangeIncidentStatusCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                ChangeIncidentStatusCommand(
                    incident_id="bad",
                    company_id="comp1",
                    new_status="triaged",
                    actor_id="user1",
                )
            )


class TestChangeSeverityCommandHandler:
    def test_changes_severity(self):
        repo = _mock_repo()
        incident = _make_incident()
        repo.find_by_id.return_value = incident
        handler = ChangeIncidentSeverityCommandHandler(incident_repo=repo)
        handler.handle(
            ChangeIncidentSeverityCommand(
                incident_id="inc1",
                company_id="comp1",
                new_severity="P1",
                actor_id="user1",
            )
        )
        assert incident.severity == IncidentSeverity.P1
        repo.save.assert_called_once()
        repo.save_timeline.assert_called_once()

    def test_not_found_raises(self):
        repo = _mock_repo()
        repo.find_by_id.return_value = None
        handler = ChangeIncidentSeverityCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                ChangeIncidentSeverityCommand(
                    incident_id="bad",
                    company_id="comp1",
                    new_severity="P1",
                    actor_id="user1",
                )
            )


class TestAssignIncidentCommandHandler:
    def test_assigns_user(self):
        repo = _mock_repo()
        incident = _make_incident()
        repo.find_by_id.return_value = incident
        handler = AssignIncidentCommandHandler(incident_repo=repo)
        handler.handle(
            AssignIncidentCommand(
                incident_id="inc1",
                company_id="comp1",
                assigned_to="tech1",
                actor_id="user1",
            )
        )
        assert incident.assigned_to == "tech1"
        repo.save.assert_called_once()
        repo.save_timeline.assert_called_once()

    def test_not_found_raises(self):
        repo = _mock_repo()
        repo.find_by_id.return_value = None
        handler = AssignIncidentCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                AssignIncidentCommand(
                    incident_id="bad",
                    company_id="comp1",
                    assigned_to="tech1",
                    actor_id="user1",
                )
            )
