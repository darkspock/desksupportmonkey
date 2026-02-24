from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.incident_bc.incident.application.queries.get_dashboard import (
    GetDashboardQuery,
    GetDashboardQueryHandler,
)
from src.incident_bc.incident.domain.entities import SecurityIncident
from src.incident_bc.incident.domain.enums import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)


def _make_incident(**overrides):
    defaults = {
        "id": "INC001",
        "company_id": "COMP001",
        "title": "Test Incident",
        "description": "Test",
        "incident_type": IncidentType.MALWARE,
        "severity": IncidentSeverity.P2,
        "status": IncidentStatus.DETECTED,
        "reported_by": "EMP001",
        "detected_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return SecurityIncident(**defaults)


class TestGetDashboard:
    def test_maps_stats_to_dto(self):
        repo = MagicMock()
        repo.get_dashboard_stats.return_value = {
            "total_active": 5,
            "total_closed": 10,
            "active_by_severity": {"P1": 1, "P2": 2, "P3": 2},
            "by_type": {"malware": 3, "phishing": 7},
            "mttc_hours": 4.5,
            "mttr_hours": 48.2,
            "upcoming_deadlines": [
                {
                    "incident_id": "INC001",
                    "incident_title": "Malware Attack",
                    "report_type": "early_warning_24h",
                    "deadline_at": "2026-01-02T00:00:00+00:00",
                    "time_remaining_seconds": 3600,
                },
            ],
            "recent_incidents": [
                _make_incident(id="INC001", title="Recent 1"),
                _make_incident(id="INC002", title="Recent 2"),
            ],
        }

        handler = GetDashboardQueryHandler(incident_repo=repo)
        result = handler.handle(GetDashboardQuery(company_id="COMP001"))

        assert result.total_active == 5
        assert result.total_closed == 10
        assert result.active_by_severity == {"P1": 1, "P2": 2, "P3": 2}
        assert result.by_type == {"malware": 3, "phishing": 7}
        assert result.mttc_hours == 4.5
        assert result.mttr_hours == 48.2

        assert len(result.upcoming_deadlines) == 1
        assert result.upcoming_deadlines[0].incident_id == "INC001"
        assert result.upcoming_deadlines[0].report_type == "early_warning_24h"
        assert result.upcoming_deadlines[0].time_remaining_seconds == 3600

        assert len(result.recent_incidents) == 2
        assert result.recent_incidents[0].id == "INC001"
        assert result.recent_incidents[0].incident_type == "malware"
        assert result.recent_incidents[0].severity == "P2"

    def test_empty_dashboard(self):
        repo = MagicMock()
        repo.get_dashboard_stats.return_value = {
            "total_active": 0,
            "total_closed": 0,
            "active_by_severity": {},
            "by_type": {},
            "mttc_hours": None,
            "mttr_hours": None,
            "upcoming_deadlines": [],
            "recent_incidents": [],
        }

        handler = GetDashboardQueryHandler(incident_repo=repo)
        result = handler.handle(GetDashboardQuery(company_id="COMP001"))

        assert result.total_active == 0
        assert result.total_closed == 0
        assert result.mttc_hours is None
        assert result.mttr_hours is None
        assert result.upcoming_deadlines == []
        assert result.recent_incidents == []

    def test_no_mttc_when_no_contained(self):
        repo = MagicMock()
        repo.get_dashboard_stats.return_value = {
            "total_active": 3,
            "total_closed": 0,
            "active_by_severity": {"P3": 3},
            "by_type": {"phishing": 3},
            "mttc_hours": None,
            "mttr_hours": None,
            "upcoming_deadlines": [],
            "recent_incidents": [
                _make_incident(id="INC001"),
                _make_incident(id="INC002"),
                _make_incident(id="INC003"),
            ],
        }

        handler = GetDashboardQueryHandler(incident_repo=repo)
        result = handler.handle(GetDashboardQuery(company_id="COMP001"))

        assert result.mttc_hours is None
        assert len(result.recent_incidents) == 3
