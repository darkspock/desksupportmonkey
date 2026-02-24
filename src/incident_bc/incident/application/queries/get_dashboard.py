from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.incident_bc.incident.domain.repository import IncidentRepositoryInterface


@dataclass
class UpcomingDeadlineDto:
    incident_id: str
    incident_title: str
    report_type: str
    deadline_at: str
    time_remaining_seconds: int


@dataclass
class RecentIncidentDto:
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    detected_at: Optional[datetime]
    created_at: Optional[datetime]


@dataclass
class DashboardDto:
    total_active: int
    total_closed: int
    active_by_severity: dict[str, int]
    by_type: dict[str, int]
    mttc_hours: Optional[float]
    mttr_hours: Optional[float]
    upcoming_deadlines: list[UpcomingDeadlineDto] = field(default_factory=list)
    recent_incidents: list[RecentIncidentDto] = field(default_factory=list)


@dataclass
class GetDashboardQuery(Query):
    company_id: str


class GetDashboardQueryHandler(QueryHandler[GetDashboardQuery, DashboardDto]):
    def __init__(self, incident_repo: IncidentRepositoryInterface):
        self.incident_repo = incident_repo

    def handle(self, query: GetDashboardQuery) -> DashboardDto:
        stats = self.incident_repo.get_dashboard_stats(query.company_id)

        deadlines = [
            UpcomingDeadlineDto(
                incident_id=d["incident_id"],
                incident_title=d["incident_title"],
                report_type=d["report_type"],
                deadline_at=d["deadline_at"],
                time_remaining_seconds=d["time_remaining_seconds"],
            )
            for d in stats.get("upcoming_deadlines", [])
        ]

        recent = [
            RecentIncidentDto(
                id=inc.id,
                title=inc.title,
                incident_type=inc.incident_type.value,
                severity=inc.severity.value,
                status=inc.status.value,
                detected_at=inc.detected_at,
                created_at=inc.created_at,
            )
            for inc in stats.get("recent_incidents", [])
        ]

        return DashboardDto(
            total_active=stats["total_active"],
            total_closed=stats["total_closed"],
            active_by_severity=stats["active_by_severity"],
            by_type=stats["by_type"],
            mttc_hours=stats.get("mttc_hours"),
            mttr_hours=stats.get("mttr_hours"),
            upcoming_deadlines=deadlines,
            recent_incidents=recent,
        )
