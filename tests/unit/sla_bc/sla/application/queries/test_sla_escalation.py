from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.request_bc.request.domain.enums import (
    RequestPriority,
    RequestStatus,
    RequestType,
)
from src.sla_bc.sla.application.queries.get_request_sla import (
    GetRequestSlaStatusQuery,
    GetRequestSlaStatusQueryHandler,
    _highest_criticality,
    compute_effective_priority,
)
from src.sla_bc.sla.domain.entities import SlaPolicy


# ------------------------------------------------------------------ #
#  Pure-function tests: compute_effective_priority
# ------------------------------------------------------------------ #


class TestComputeEffectivePriority:
    """Tests for the pure escalation function."""

    # --- CRITICAL asset criticality ---

    def test_critical_asset_escalates_low_to_medium(self):
        priority, escalated = compute_effective_priority("low", ["critical"])
        assert priority == "medium"
        assert escalated is True

    def test_critical_asset_escalates_medium_to_high(self):
        priority, escalated = compute_effective_priority("medium", ["critical"])
        assert priority == "high"
        assert escalated is True

    def test_critical_asset_escalates_high_to_urgent(self):
        priority, escalated = compute_effective_priority("high", ["critical"])
        assert priority == "urgent"
        assert escalated is True

    def test_critical_asset_does_not_escalate_urgent(self):
        priority, escalated = compute_effective_priority("urgent", ["critical"])
        assert priority == "urgent"
        assert escalated is False

    # --- HIGH asset criticality ---

    def test_high_asset_escalates_low_to_medium(self):
        priority, escalated = compute_effective_priority("low", ["high"])
        assert priority == "medium"
        assert escalated is True

    def test_high_asset_does_not_escalate_medium(self):
        priority, escalated = compute_effective_priority("medium", ["high"])
        assert priority == "medium"
        assert escalated is False

    def test_high_asset_does_not_escalate_high(self):
        priority, escalated = compute_effective_priority("high", ["high"])
        assert priority == "high"
        assert escalated is False

    def test_high_asset_does_not_escalate_urgent(self):
        priority, escalated = compute_effective_priority("urgent", ["high"])
        assert priority == "urgent"
        assert escalated is False

    # --- MEDIUM asset criticality ---

    def test_medium_asset_no_escalation_for_low(self):
        priority, escalated = compute_effective_priority("low", ["medium"])
        assert priority == "low"
        assert escalated is False

    def test_medium_asset_no_escalation_for_medium(self):
        priority, escalated = compute_effective_priority("medium", ["medium"])
        assert priority == "medium"
        assert escalated is False

    def test_medium_asset_no_escalation_for_high(self):
        priority, escalated = compute_effective_priority("high", ["medium"])
        assert priority == "high"
        assert escalated is False

    def test_medium_asset_no_escalation_for_urgent(self):
        priority, escalated = compute_effective_priority("urgent", ["medium"])
        assert priority == "urgent"
        assert escalated is False

    # --- LOW asset criticality ---

    def test_low_asset_no_escalation_for_low(self):
        priority, escalated = compute_effective_priority("low", ["low"])
        assert priority == "low"
        assert escalated is False

    def test_low_asset_no_escalation_for_medium(self):
        priority, escalated = compute_effective_priority("medium", ["low"])
        assert priority == "medium"
        assert escalated is False

    def test_low_asset_no_escalation_for_high(self):
        priority, escalated = compute_effective_priority("high", ["low"])
        assert priority == "high"
        assert escalated is False

    def test_low_asset_no_escalation_for_urgent(self):
        priority, escalated = compute_effective_priority("urgent", ["low"])
        assert priority == "urgent"
        assert escalated is False

    # --- Empty criticalities ---

    def test_empty_criticalities_no_escalation(self):
        priority, escalated = compute_effective_priority("low", [])
        assert priority == "low"
        assert escalated is False

    def test_empty_criticalities_preserves_any_priority(self):
        for p in ("low", "medium", "high", "urgent"):
            priority, escalated = compute_effective_priority(p, [])
            assert priority == p
            assert escalated is False

    # --- Multiple criticalities (uses highest) ---

    def test_multiple_criticalities_uses_highest_critical(self):
        priority, escalated = compute_effective_priority(
            "low", ["low", "critical"],
        )
        assert priority == "medium"
        assert escalated is True

    def test_multiple_criticalities_uses_highest_high(self):
        priority, escalated = compute_effective_priority(
            "low", ["low", "medium", "high"],
        )
        assert priority == "medium"
        assert escalated is True

    def test_multiple_criticalities_all_low_no_escalation(self):
        priority, escalated = compute_effective_priority(
            "medium", ["low", "low", "low"],
        )
        assert priority == "medium"
        assert escalated is False


# ------------------------------------------------------------------ #
#  Pure-function tests: _highest_criticality
# ------------------------------------------------------------------ #


class TestHighestCriticality:
    def test_single_critical(self):
        assert _highest_criticality(["critical"]) == "critical"

    def test_single_low(self):
        assert _highest_criticality(["low"]) == "low"

    def test_mixed_returns_highest(self):
        assert _highest_criticality(["low", "high", "medium"]) == "high"

    def test_critical_wins_over_all(self):
        assert _highest_criticality(["medium", "critical", "high"]) == "critical"

    def test_two_identical_returns_same(self):
        assert _highest_criticality(["medium", "medium"]) == "medium"

    def test_unknown_criticality_treated_as_zero(self):
        # Unknown gets order 0, so "low" (order 1) wins
        assert _highest_criticality(["unknown", "low"]) == "low"


# ------------------------------------------------------------------ #
#  Handler-level escalation tests
# ------------------------------------------------------------------ #


def _make_mock_request(
    priority: RequestPriority = RequestPriority.LOW,
    affected_asset_ids: list[str] | None = None,
    hours_ago: float = 2,
):
    now = datetime.now(timezone.utc)
    req = MagicMock()
    req.id = "r1"
    req.company_id = "c1"
    req.priority = priority
    req.type = RequestType.INCIDENT
    req.status = RequestStatus.IN_PROGRESS
    req.created_by = "u1"
    req.created_at = now - timedelta(hours=hours_ago)
    req.first_response_at = None
    req.resolved_at = None
    req.data = {}
    if affected_asset_ids:
        req.data["affected_asset_ids"] = affected_asset_ids
    return req


def _make_mock_asset(asset_id: str, criticality: str):
    asset = MagicMock()
    asset.id = asset_id
    asset.criticality = MagicMock()
    asset.criticality.value = criticality
    return asset


class TestSlaEscalationHandler:
    """Handler-level tests for escalation within GetRequestSlaStatusQueryHandler."""

    def setup_method(self):
        self.sla_repo = MagicMock()
        self.request_repo = MagicMock()
        self.asset_repo = MagicMock()
        self.escalation_config_repo = MagicMock()
        self.handler = GetRequestSlaStatusQueryHandler(
            sla_repo=self.sla_repo,
            request_repo=self.request_repo,
            asset_repo=self.asset_repo,
            escalation_config_repo=self.escalation_config_repo,
        )
        self.query = GetRequestSlaStatusQuery(
            request_id="r1", company_id="c1",
        )

    def test_escalation_enabled_with_critical_asset(self):
        """LOW priority + CRITICAL asset -> escalated to MEDIUM, policy looked up with medium."""
        request = _make_mock_request(
            priority=RequestPriority.LOW,
            affected_asset_ids=["a1"],
        )
        self.request_repo.find_by_id.return_value = request

        asset = _make_mock_asset("a1", "critical")
        self.asset_repo.find_by_ids.return_value = [asset]

        config = MagicMock()
        config.enabled = True
        self.escalation_config_repo.find_by_company.return_value = config

        policy = SlaPolicy.create(
            company_id="c1",
            name="Medium SLA",
            priority="medium",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        self.sla_repo.find_policy_for_request.return_value = policy

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.escalated is True
        assert result.effective_priority == "medium"
        assert result.original_priority == "low"
        # Policy was looked up with the escalated priority
        self.sla_repo.find_policy_for_request.assert_called_once_with(
            company_id="c1",
            priority="medium",
            request_type=RequestType.INCIDENT,
        )

    def test_escalation_disabled_via_config(self):
        """When escalation config disabled, no escalation occurs."""
        request = _make_mock_request(
            priority=RequestPriority.LOW,
            affected_asset_ids=["a1"],
        )
        self.request_repo.find_by_id.return_value = request

        config = MagicMock()
        config.enabled = False
        self.escalation_config_repo.find_by_company.return_value = config

        policy = SlaPolicy.create(
            company_id="c1",
            name="Low SLA",
            priority="low",
            response_time_hours=8,
            resolution_time_hours=48,
        )
        self.sla_repo.find_policy_for_request.return_value = policy

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.escalated is False
        assert result.effective_priority == "low"
        assert result.original_priority == "low"
        # Asset repo should NOT be called
        self.asset_repo.find_by_ids.assert_not_called()

    def test_escalation_default_enabled_when_no_config(self):
        """When no config exists, escalation defaults to enabled."""
        request = _make_mock_request(
            priority=RequestPriority.LOW,
            affected_asset_ids=["a1"],
        )
        self.request_repo.find_by_id.return_value = request

        asset = _make_mock_asset("a1", "critical")
        self.asset_repo.find_by_ids.return_value = [asset]

        # No config found -> defaults to enabled
        self.escalation_config_repo.find_by_company.return_value = None

        policy = SlaPolicy.create(
            company_id="c1",
            name="Medium SLA",
            priority="medium",
            response_time_hours=4,
            resolution_time_hours=24,
        )
        self.sla_repo.find_policy_for_request.return_value = policy

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.escalated is True
        assert result.effective_priority == "medium"

    def test_no_escalation_without_affected_assets(self):
        """Request without affected asset IDs -> no escalation."""
        request = _make_mock_request(priority=RequestPriority.LOW)
        self.request_repo.find_by_id.return_value = request

        config = MagicMock()
        config.enabled = True
        self.escalation_config_repo.find_by_company.return_value = config

        policy = SlaPolicy.create(
            company_id="c1",
            name="Low SLA",
            priority="low",
            response_time_hours=8,
            resolution_time_hours=48,
        )
        self.sla_repo.find_policy_for_request.return_value = policy

        result = self.handler.handle(self.query)

        assert result is not None
        assert result.escalated is False
        assert result.effective_priority == "low"

    def test_no_escalation_without_repos(self):
        """Handler without asset_repo / escalation_config_repo skips escalation."""
        handler_no_repos = GetRequestSlaStatusQueryHandler(
            sla_repo=self.sla_repo,
            request_repo=self.request_repo,
        )
        request = _make_mock_request(
            priority=RequestPriority.LOW,
            affected_asset_ids=["a1"],
        )
        self.request_repo.find_by_id.return_value = request

        policy = SlaPolicy.create(
            company_id="c1",
            name="Low SLA",
            priority="low",
            response_time_hours=8,
            resolution_time_hours=48,
        )
        self.sla_repo.find_policy_for_request.return_value = policy

        result = handler_no_repos.handle(self.query)

        assert result is not None
        assert result.escalated is False
        assert result.effective_priority == "low"
