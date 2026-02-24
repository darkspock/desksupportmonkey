from unittest.mock import MagicMock

import pytest

from src.incident_bc.incident.application.commands.create_postmortem import (
    CreatePostMortemCommand,
    CreatePostMortemCommandHandler,
)
from src.incident_bc.incident.application.commands.update_postmortem import (
    UpdatePostMortemCommand,
    UpdatePostMortemCommandHandler,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from src.incident_bc.incident.domain.exceptions import (
    IncidentNotClosableForPostMortemError,
    IncidentNotFoundError,
    PostMortemAlreadyExistsError,
    PostMortemNotFoundError,
)

from datetime import datetime, timezone


def _make_incident(status: IncidentStatus = IncidentStatus.RECOVERED) -> SecurityIncident:
    return SecurityIncident(
        id="INC001",
        company_id="COMP001",
        title="Test Incident",
        description="Test description",
        incident_type=IncidentType.MALWARE,
        severity=IncidentSeverity.P2,
        status=status,
        reported_by="USER001",
        detected_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestCreatePostMortem:
    def test_create_postmortem_happy_path(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.RECOVERED)
        repo.find_postmortem_by_incident.return_value = None

        handler = CreatePostMortemCommandHandler(incident_repo=repo)
        handler.handle(
            CreatePostMortemCommand(
                incident_id="INC001",
                company_id="COMP001",
                root_cause="Root cause analysis",
                lessons_learned="Key lessons",
                corrective_actions="Actions taken",
                actor_id="ADMIN001",
            )
        )

        repo.save_postmortem.assert_called_once()
        pm_dict = repo.save_postmortem.call_args[0][0]
        assert pm_dict["incident_id"] == "INC001"
        assert pm_dict["root_cause"] == "Root cause analysis"
        assert pm_dict["lessons_learned"] == "Key lessons"
        assert pm_dict["corrective_actions"] == "Actions taken"
        assert pm_dict["created_by"] == "ADMIN001"

        repo.save_timeline.assert_called_once()
        timeline_entry = repo.save_timeline.call_args[0][0]
        assert timeline_entry.event_type.value == "postmortem_created"

    def test_create_postmortem_closed_incident(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.CLOSED)
        repo.find_postmortem_by_incident.return_value = None

        handler = CreatePostMortemCommandHandler(incident_repo=repo)
        handler.handle(
            CreatePostMortemCommand(
                incident_id="INC001",
                company_id="COMP001",
                root_cause="Root cause",
                lessons_learned="Lessons",
                corrective_actions="Actions",
                actor_id="ADMIN001",
            )
        )

        repo.save_postmortem.assert_called_once()

    def test_create_postmortem_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = CreatePostMortemCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                CreatePostMortemCommand(
                    incident_id="INC999",
                    company_id="COMP001",
                    root_cause="Root cause",
                    lessons_learned="Lessons",
                    corrective_actions="Actions",
                    actor_id="ADMIN001",
                )
            )

    def test_create_postmortem_wrong_status(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.DETECTED)

        handler = CreatePostMortemCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotClosableForPostMortemError):
            handler.handle(
                CreatePostMortemCommand(
                    incident_id="INC001",
                    company_id="COMP001",
                    root_cause="Root cause",
                    lessons_learned="Lessons",
                    corrective_actions="Actions",
                    actor_id="ADMIN001",
                )
            )

    def test_create_postmortem_already_exists(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.RECOVERED)
        repo.find_postmortem_by_incident.return_value = {"id": "PM001"}

        handler = CreatePostMortemCommandHandler(incident_repo=repo)
        with pytest.raises(PostMortemAlreadyExistsError):
            handler.handle(
                CreatePostMortemCommand(
                    incident_id="INC001",
                    company_id="COMP001",
                    root_cause="Root cause",
                    lessons_learned="Lessons",
                    corrective_actions="Actions",
                    actor_id="ADMIN001",
                )
            )


class TestUpdatePostMortem:
    def test_update_postmortem_happy_path(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.RECOVERED)
        repo.find_postmortem_by_incident.return_value = {
            "id": "PM001",
            "incident_id": "INC001",
            "root_cause": "Old root cause",
            "lessons_learned": "Old lessons",
            "corrective_actions": "Old actions",
            "created_by": "ADMIN001",
        }

        handler = UpdatePostMortemCommandHandler(incident_repo=repo)
        handler.handle(
            UpdatePostMortemCommand(
                incident_id="INC001",
                company_id="COMP001",
                root_cause="Updated root cause",
                actor_id="ADMIN001",
            )
        )

        repo.save_postmortem.assert_called_once()
        update_dict = repo.save_postmortem.call_args[0][0]
        assert update_dict["root_cause"] == "Updated root cause"

        repo.save_timeline.assert_called_once()
        timeline_entry = repo.save_timeline.call_args[0][0]
        assert timeline_entry.event_type.value == "postmortem_updated"

    def test_update_postmortem_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident(IncidentStatus.RECOVERED)
        repo.find_postmortem_by_incident.return_value = None

        handler = UpdatePostMortemCommandHandler(incident_repo=repo)
        with pytest.raises(PostMortemNotFoundError):
            handler.handle(
                UpdatePostMortemCommand(
                    incident_id="INC001",
                    company_id="COMP001",
                    root_cause="New root cause",
                    actor_id="ADMIN001",
                )
            )

    def test_update_postmortem_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UpdatePostMortemCommandHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                UpdatePostMortemCommand(
                    incident_id="INC999",
                    company_id="COMP001",
                    root_cause="New root cause",
                    actor_id="ADMIN001",
                )
            )
