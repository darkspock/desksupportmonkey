from dataclasses import dataclass, field
from datetime import datetime

from src.framework.application.query_bus import Query, QueryHandler
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class ComplianceByGroupDto:
    group: str
    total: int
    met: int
    breached: int
    compliance_pct: float


@dataclass
class BreachTrendPointDto:
    period: str
    count: int


@dataclass
class SlaDashboardDto:
    total_resolved: int
    met: int
    breached: int
    compliance_pct: float
    by_priority: list[ComplianceByGroupDto] = field(default_factory=list)
    by_type: list[ComplianceByGroupDto] = field(default_factory=list)
    breach_trend: list[BreachTrendPointDto] = field(default_factory=list)


@dataclass
class GetSlaDashboardQuery(Query):
    company_id: str
    from_date: datetime
    to_date: datetime
    bucket: str = "week"


class GetSlaDashboardQueryHandler(
    QueryHandler[GetSlaDashboardQuery, SlaDashboardDto]
):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, query: GetSlaDashboardQuery) -> SlaDashboardDto:
        stats = self.sla_repo.compliance_stats(
            query.company_id, query.from_date, query.to_date
        )
        by_priority_raw = self.sla_repo.compliance_by_priority(
            query.company_id, query.from_date, query.to_date
        )
        by_type_raw = self.sla_repo.compliance_by_type(
            query.company_id, query.from_date, query.to_date
        )
        trend_raw = self.sla_repo.breach_trend(
            query.company_id, query.from_date, query.to_date, query.bucket
        )

        by_priority = [
            ComplianceByGroupDto(
                group=row["priority"],
                total=row["total"],
                met=row["met"],
                breached=row["breached"],
                compliance_pct=row["compliance_pct"],
            )
            for row in by_priority_raw
        ]
        by_type = [
            ComplianceByGroupDto(
                group=row["type"],
                total=row["total"],
                met=row["met"],
                breached=row["breached"],
                compliance_pct=row["compliance_pct"],
            )
            for row in by_type_raw
        ]
        breach_trend = [
            BreachTrendPointDto(period=row["period"], count=row["count"])
            for row in trend_raw
        ]

        return SlaDashboardDto(
            total_resolved=stats.get("total_resolved", 0),
            met=stats.get("met", 0),
            breached=stats.get("breached", 0),
            compliance_pct=stats.get("compliance_pct", 0.0),
            by_priority=by_priority,
            by_type=by_type,
            breach_trend=breach_trend,
        )
