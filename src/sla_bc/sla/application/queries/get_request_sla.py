from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.asset_bc.asset.domain.repository import AssetRepositoryInterface
from src.company_bc.sla_escalation_config.domain.repository import (
    SlaEscalationConfigRepositoryInterface,
)
from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.repository import RequestRepositoryInterface
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


# --- Escalation pure functions ---

PRIORITY_ESCALATION_MAP = {
    "low": "medium",
    "medium": "high",
    "high": "urgent",
    "urgent": "urgent",
}

CRITICALITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _highest_criticality(criticalities: list[str]) -> str:
    return max(criticalities, key=lambda c: CRITICALITY_ORDER.get(c, 0))


def compute_effective_priority(
    request_priority: str,
    affected_asset_criticalities: list[str],
) -> tuple[str, bool]:
    """Returns (effective_priority, escalated)."""
    if not affected_asset_criticalities:
        return request_priority, False

    max_criticality = _highest_criticality(affected_asset_criticalities)

    if max_criticality == "critical":
        escalated_priority = PRIORITY_ESCALATION_MAP.get(
            request_priority, request_priority,
        )
        if escalated_priority != request_priority:
            return escalated_priority, True
    elif max_criticality == "high" and request_priority == "low":
        return "medium", True

    return request_priority, False


# --- DTO ---

@dataclass
class SlaStatusDto:
    policy_name: Optional[str]
    response_target_hours: Optional[float]
    resolution_target_hours: Optional[float]
    response_elapsed_hours: float
    resolution_elapsed_hours: float
    response_status: str  # on_track | warning | breached | met
    resolution_status: str  # on_track | warning | breached | met
    response_remaining_hours: Optional[float]
    resolution_remaining_hours: Optional[float]
    escalated: bool = False
    effective_priority: Optional[str] = None
    original_priority: Optional[str] = None


@dataclass
class GetRequestSlaStatusQuery(Query):
    request_id: str
    company_id: str


class GetRequestSlaStatusQueryHandler(
    QueryHandler[GetRequestSlaStatusQuery, Optional[SlaStatusDto]]
):
    def __init__(
        self,
        sla_repo: SlaRepositoryInterface,
        request_repo: RequestRepositoryInterface,
        asset_repo: Optional[AssetRepositoryInterface] = None,
        escalation_config_repo: Optional[SlaEscalationConfigRepositoryInterface] = None,
    ):
        self.sla_repo = sla_repo
        self.request_repo = request_repo
        self.asset_repo = asset_repo
        self.escalation_config_repo = escalation_config_repo

    def handle(
        self, query: GetRequestSlaStatusQuery
    ) -> Optional[SlaStatusDto]:
        request = self.request_repo.find_by_id(
            query.request_id, query.company_id
        )
        if not request:
            return None

        # Determine effective priority (with optional escalation)
        original_priority = request.priority.value
        effective_priority = original_priority
        escalated = False

        if self.asset_repo and self.escalation_config_repo:
            escalation_enabled = True
            config = self.escalation_config_repo.find_by_company(
                query.company_id,
            )
            if config is not None:
                escalation_enabled = config.enabled

            if escalation_enabled:
                affected_ids = []
                if request.data:
                    affected_ids = request.data.get(
                        "affected_asset_ids", [],
                    )
                if affected_ids:
                    assets = self.asset_repo.find_by_ids(
                        affected_ids, query.company_id,
                    )
                    criticalities = [
                        a.criticality.value
                        for a in assets
                        if a.criticality
                    ]
                    effective_priority, escalated = (
                        compute_effective_priority(
                            original_priority, criticalities,
                        )
                    )

        policy = self.sla_repo.find_policy_for_request(
            company_id=query.company_id,
            priority=effective_priority,
            request_type=request.type,
        )
        if not policy:
            return None

        now = datetime.now(timezone.utc)
        created = request.created_at or now
        # Ensure timezone-aware comparison
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        # Response time
        if request.first_response_at:
            response_elapsed = (
                request.first_response_at - created
            ).total_seconds() / 3600
        else:
            response_elapsed = (now - created).total_seconds() / 3600

        # Resolution time (subtract SLA paused time)
        paused_seconds = request.sla_paused_total_seconds or 0
        if request.sla_paused_at:
            sla_paused_at = request.sla_paused_at
            if sla_paused_at.tzinfo is None:
                sla_paused_at = sla_paused_at.replace(tzinfo=timezone.utc)
            paused_seconds += int((now - sla_paused_at).total_seconds())

        if request.resolved_at:
            resolution_elapsed = (
                (request.resolved_at - created).total_seconds() - paused_seconds
            ) / 3600
        else:
            resolution_elapsed = (
                (now - created).total_seconds() - paused_seconds
            ) / 3600

        response_elapsed = round(response_elapsed, 2)
        resolution_elapsed = max(0, round(resolution_elapsed, 2))

        # Determine response status
        warning_pct = policy.warning_threshold_pct / 100
        response_target = policy.response_time_hours
        resolution_target = policy.resolution_time_hours

        if request.first_response_at:
            response_status = (
                "breached"
                if response_elapsed >= response_target
                else "met"
            )
        elif response_elapsed >= response_target:
            response_status = "breached"
        elif response_elapsed >= response_target * warning_pct:
            response_status = "warning"
        else:
            response_status = "on_track"

        if request.resolved_at:
            resolution_status = (
                "breached"
                if resolution_elapsed >= resolution_target
                else "met"
            )
        elif resolution_elapsed >= resolution_target:
            resolution_status = "breached"
        elif resolution_elapsed >= resolution_target * warning_pct:
            resolution_status = "warning"
        else:
            resolution_status = "on_track"

        response_remaining = (
            round(response_target - response_elapsed, 2)
            if not request.first_response_at
            else None
        )
        resolution_remaining = (
            round(resolution_target - resolution_elapsed, 2)
            if not request.resolved_at
            else None
        )

        return SlaStatusDto(
            policy_name=policy.name,
            response_target_hours=response_target,
            resolution_target_hours=resolution_target,
            response_elapsed_hours=response_elapsed,
            resolution_elapsed_hours=resolution_elapsed,
            response_status=response_status,
            resolution_status=resolution_status,
            response_remaining_hours=response_remaining,
            resolution_remaining_hours=resolution_remaining,
            escalated=escalated,
            effective_priority=effective_priority,
            original_priority=original_priority,
        )
