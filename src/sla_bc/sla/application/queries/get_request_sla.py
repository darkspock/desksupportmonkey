from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.request_bc.request.domain.repository import RequestRepositoryInterface
from src.sla_bc.sla.domain.enums import SlaBreachType
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


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
    ):
        self.sla_repo = sla_repo
        self.request_repo = request_repo

    def handle(
        self, query: GetRequestSlaStatusQuery
    ) -> Optional[SlaStatusDto]:
        request = self.request_repo.find_by_id(
            query.request_id, query.company_id
        )
        if not request:
            return None

        policy = self.sla_repo.find_policy_for_request(
            company_id=query.company_id,
            priority=request.priority.value,
            request_type=request.type,
        )
        if not policy:
            return None

        now = datetime.now(timezone.utc)
        created = request.created_at or now

        # Response time: from created_at to first_response_at (or now if not yet responded)
        if request.first_response_at:
            response_elapsed = (
                request.first_response_at - created
            ).total_seconds() / 3600
        else:
            response_elapsed = (now - created).total_seconds() / 3600

        # Resolution time: from created_at to resolved_at (or now if still open)
        if request.resolved_at:
            resolution_elapsed = (
                request.resolved_at - created
            ).total_seconds() / 3600
        else:
            resolution_elapsed = (now - created).total_seconds() / 3600

        response_elapsed = round(response_elapsed, 2)
        resolution_elapsed = round(resolution_elapsed, 2)

        # Determine response status
        warning_pct = policy.warning_threshold_pct / 100
        response_target = policy.response_time_hours
        resolution_target = policy.resolution_time_hours

        if request.first_response_at:
            # Already responded
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
        )
