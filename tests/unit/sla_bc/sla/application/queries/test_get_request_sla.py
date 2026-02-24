from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import (
    RequestPriority,
    RequestStatus,
    RequestType,
)
from src.sla_bc.sla.application.queries.get_request_sla import (
    GetRequestSlaStatusQuery,
    GetRequestSlaStatusQueryHandler,
)
from src.sla_bc.sla.domain.entities import SlaPolicy


def _make_request(
    hours_ago: float = 2,
    first_response_hours_ago: float | None = None,
    resolved_hours_ago: float | None = None,
) -> ServiceRequest:
    now = datetime.now(timezone.utc)
    req = ServiceRequest(
        id="r1",
        company_id="c1",
        created_by="u1",
        type=RequestType.INCIDENT,
        title="Test",
        description="Test",
        status=RequestStatus.IN_PROGRESS,
        priority=RequestPriority.HIGH,
        created_at=now - timedelta(hours=hours_ago),
    )
    if first_response_hours_ago is not None:
        req.first_response_at = now - timedelta(hours=first_response_hours_ago)
    if resolved_hours_ago is not None:
        req.resolved_at = now - timedelta(hours=resolved_hours_ago)
        req.status = RequestStatus.RESOLVED
    return req


def _make_policy(
    response_hours: float = 4,
    resolution_hours: float = 24,
    warning_pct: int = 75,
) -> SlaPolicy:
    return SlaPolicy.create(
        company_id="c1",
        name="Test SLA",
        priority="high",
        response_time_hours=response_hours,
        resolution_time_hours=resolution_hours,
        warning_threshold_pct=warning_pct,
    )


class TestGetRequestSlaStatus:
    def setup_method(self):
        self.sla_repo = MagicMock()
        self.request_repo = MagicMock()
        self.handler = GetRequestSlaStatusQueryHandler(
            sla_repo=self.sla_repo,
            request_repo=self.request_repo,
        )
        self.query = GetRequestSlaStatusQuery(
            request_id="r1", company_id="c1"
        )

    def test_returns_none_when_no_request(self):
        self.request_repo.find_by_id.return_value = None
        result = self.handler.handle(self.query)
        assert result is None

    def test_returns_none_when_no_policy(self):
        self.request_repo.find_by_id.return_value = _make_request()
        self.sla_repo.find_policy_for_request.return_value = None
        result = self.handler.handle(self.query)
        assert result is None

    def test_on_track_status(self):
        self.request_repo.find_by_id.return_value = _make_request(hours_ago=1)
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.policy_name == "Test SLA"
        assert result.response_status == "on_track"
        assert result.resolution_status == "on_track"
        assert result.response_remaining_hours is not None
        assert result.response_remaining_hours > 0

    def test_warning_status(self):
        # 75% of 4h = 3h, so at 3.5h we should be in warning
        self.request_repo.find_by_id.return_value = _make_request(hours_ago=3.5)
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.response_status == "warning"

    def test_breached_status(self):
        # Over 4h response target
        self.request_repo.find_by_id.return_value = _make_request(hours_ago=5)
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.response_status == "breached"

    def test_met_when_responded_on_time(self):
        # Responded at 1h ago, created 2h ago -> 1h response time, under 4h target
        self.request_repo.find_by_id.return_value = _make_request(
            hours_ago=2, first_response_hours_ago=1
        )
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.response_status == "met"
        assert result.response_remaining_hours is None

    def test_resolution_met(self):
        # Resolved at 1h ago, created 10h ago -> 9h resolution time, under 24h
        self.request_repo.find_by_id.return_value = _make_request(
            hours_ago=10,
            first_response_hours_ago=9,
            resolved_hours_ago=1,
        )
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.resolution_status == "met"
        assert result.resolution_remaining_hours is None

    def test_resolution_breached(self):
        self.request_repo.find_by_id.return_value = _make_request(hours_ago=25)
        self.sla_repo.find_policy_for_request.return_value = _make_policy()

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.resolution_status == "breached"
