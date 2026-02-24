from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.incident_bc.incident.application.queries.list_reports import (
    ListReportsQuery,
    ListReportsQueryHandler,
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
from src.incident_bc.incident.domain.exceptions import IncidentNotFoundError

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


def _make_reports() -> list[RegulatoryReport]:
    return RegulatoryReport.create_for_incident("inc1", NOW)


class TestListReportsQueryHandler:
    def test_returns_reports_with_countdown(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        reports = _make_reports()
        repo.find_reports_by_incident.return_value = reports

        handler = ListReportsQueryHandler(incident_repo=repo)
        result = handler.handle(
            ListReportsQuery(incident_id="inc1", company_id="comp1")
        )

        assert len(result) == 3
        for dto in result:
            assert dto.time_remaining_seconds is not None
            assert dto.elapsed_percentage is not None
            assert dto.time_remaining_seconds >= 0
            assert 0 <= dto.elapsed_percentage <= 100

    def test_report_types_are_correct(self):
        repo = MagicMock()
        repo.find_by_id.return_value = _make_incident()
        repo.find_reports_by_incident.return_value = _make_reports()

        handler = ListReportsQueryHandler(incident_repo=repo)
        result = handler.handle(
            ListReportsQuery(incident_id="inc1", company_id="comp1")
        )

        types = {r.report_type for r in result}
        assert types == {"early_warning_24h", "detailed_72h", "final_30d"}

    def test_raises_when_incident_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = ListReportsQueryHandler(incident_repo=repo)
        with pytest.raises(IncidentNotFoundError):
            handler.handle(
                ListReportsQuery(incident_id="inc1", company_id="comp1")
            )
