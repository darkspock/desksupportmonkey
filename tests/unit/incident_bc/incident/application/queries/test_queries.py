from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.incident_bc.incident.application.queries.get_incident_detail import (
    GetIncidentDetailQuery,
    GetIncidentDetailQueryHandler,
)
from src.incident_bc.incident.application.queries.list_incidents import (
    ListIncidentsQuery,
    ListIncidentsQueryHandler,
)
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
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError

NOW = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_incident(incident_id: str = "inc1") -> SecurityIncident:
    return SecurityIncident.create(
        company_id="comp1",
        title="Phishing",
        description="Phishing email",
        incident_type=IncidentType.PHISHING,
        severity=IncidentSeverity.P2,
        detected_at=NOW,
        reported_by="user1",
        id=incident_id,
    )


def _make_timeline_entry(
    incident_id: str = "inc1",
) -> IncidentTimeline:
    return IncidentTimeline.create(
        incident_id=incident_id,
        event_type=TimelineEventType.INCIDENT_CREATED,
        description="Incident created",
        actor_id="user1",
    )


class TestListIncidentsQueryHandler:
    def test_returns_paginated_results(self):
        repo = MagicMock()
        incidents = [_make_incident("inc1"), _make_incident("inc2")]
        repo.find_all.return_value = (incidents, 2)
        handler = ListIncidentsQueryHandler(incident_repo=repo)

        items, total = handler.handle(
            ListIncidentsQuery(company_id="comp1", page=1, page_size=20)
        )
        assert total == 2
        assert len(items) == 2
        assert items[0].id == "inc1"
        assert items[0].incident_type == "phishing"
        assert items[0].severity == "P2"
        assert items[0].status == "detected"

    def test_returns_empty_for_no_results(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListIncidentsQueryHandler(incident_repo=repo)

        items, total = handler.handle(
            ListIncidentsQuery(company_id="comp1")
        )
        assert total == 0
        assert items == []

    def test_resolves_user_names(self):
        repo = MagicMock()
        incident = _make_incident()
        incident.assigned_to = "tech1"
        repo.find_all.return_value = ([incident], 1)

        name_resolver = MagicMock(return_value={"tech1": "Tech User"})
        handler = ListIncidentsQueryHandler(
            incident_repo=repo, user_name_resolver=name_resolver
        )

        items, total = handler.handle(
            ListIncidentsQuery(company_id="comp1")
        )
        assert items[0].assigned_to_name == "Tech User"
        name_resolver.assert_called_once()


class TestGetIncidentDetailQueryHandler:
    def test_returns_full_detail(self):
        repo = MagicMock()
        incident = _make_incident()
        timeline = [_make_timeline_entry()]
        repo.find_by_id.return_value = incident
        repo.find_timeline.return_value = timeline
        repo.find_reports_by_incident.return_value = []
        repo.find_assets_by_incident.return_value = []
        repo.find_vendors_by_incident.return_value = []
        repo.find_postmortem_by_incident.return_value = None

        handler = GetIncidentDetailQueryHandler(incident_repo=repo)
        detail = handler.handle(
            GetIncidentDetailQuery(incident_id="inc1", company_id="comp1")
        )

        assert detail.id == "inc1"
        assert detail.title == "Phishing"
        assert detail.incident_type == "phishing"
        assert detail.severity == "P2"
        assert detail.status == "detected"
        assert detail.reported_by == "user1"
        assert len(detail.timeline) == 1
        assert detail.timeline[0].event_type == "incident_created"

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetIncidentDetailQueryHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                GetIncidentDetailQuery(incident_id="bad", company_id="comp1")
            )

    def test_resolves_user_names(self):
        repo = MagicMock()
        incident = _make_incident()
        incident.assigned_to = "tech1"
        repo.find_by_id.return_value = incident
        repo.find_timeline.return_value = []
        repo.find_reports_by_incident.return_value = []
        repo.find_assets_by_incident.return_value = []
        repo.find_vendors_by_incident.return_value = []
        repo.find_postmortem_by_incident.return_value = None

        name_resolver = MagicMock(
            return_value={"user1": "Reporter", "tech1": "Technician"}
        )
        handler = GetIncidentDetailQueryHandler(
            incident_repo=repo, user_name_resolver=name_resolver
        )
        detail = handler.handle(
            GetIncidentDetailQuery(incident_id="inc1", company_id="comp1")
        )
        assert detail.reported_by_name == "Reporter"
        assert detail.assigned_to_name == "Technician"
