from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class RiskDashboardDto:
    total_risks: int
    open_risks: int
    mitigated_risks: int
    accepted_risks: int
    by_level: dict[str, int]
    by_category: dict[str, int]
    heat_map: list[dict]
    overdue_reviews: int
    recent_risks: list[dict]


@dataclass
class GetRiskDashboardQuery(Query):
    company_id: str


class GetRiskDashboardQueryHandler(QueryHandler[GetRiskDashboardQuery, RiskDashboardDto]):
    def __init__(
        self,
        risk_repo: RiskRepositoryInterface,
        user_name_resolver: Optional[object] = None,
    ):
        self.risk_repo = risk_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: GetRiskDashboardQuery) -> RiskDashboardDto:
        stats = self.risk_repo.get_dashboard_stats(query.company_id)

        recent_risks = []
        for risk in stats["recent_risks"]:
            recent_risks.append({
                "id": risk.id,
                "title": risk.title,
                "category": risk.category,
                "status": risk.status,
                "risk_level": risk.risk_level,
                "created_at": risk.created_at.isoformat() if risk.created_at else None,
            })

        return RiskDashboardDto(
            total_risks=stats["total_risks"],
            open_risks=stats["open_risks"],
            mitigated_risks=stats["mitigated_risks"],
            accepted_risks=stats["accepted_risks"],
            by_level=stats["by_level"],
            by_category=stats["by_category"],
            heat_map=stats["heat_map"],
            overdue_reviews=stats["overdue_reviews"],
            recent_risks=recent_risks,
        )
