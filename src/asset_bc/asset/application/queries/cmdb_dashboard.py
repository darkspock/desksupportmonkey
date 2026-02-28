from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
    CIRelationshipRepositoryInterface,
)
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class MostDependedAssetDto:
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    incoming_count: int


@dataclass
class OverdueBIAReviewDto:
    asset_id: str
    asset_name: str
    asset_tag: Optional[str]
    criticality: str
    bia_reviewed_at: Optional[datetime]


@dataclass
class CMDBDashboardDto:
    criticality_distribution: dict[str, int] = field(default_factory=dict)
    orphan_critical_count: int = 0
    bia_total_critical_high: int = 0
    bia_has_coverage: int = 0
    bia_coverage_pct: float = 0.0
    total_relationships: int = 0
    relationships_by_type: dict[str, int] = field(default_factory=dict)
    most_depended_upon: list[MostDependedAssetDto] = field(default_factory=list)
    overdue_bia_reviews: list[OverdueBIAReviewDto] = field(default_factory=list)


@dataclass
class GetCMDBDashboardQuery(Query):
    company_id: str


class GetCMDBDashboardQueryHandler(
    QueryHandler[GetCMDBDashboardQuery, CMDBDashboardDto]
):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        ci_repo: CIRelationshipRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.ci_repo = ci_repo

    def handle(self, query: GetCMDBDashboardQuery) -> CMDBDashboardDto:
        company_id = query.company_id

        criticality_distribution = self.asset_repo.count_by_criticality(company_id)
        orphan_critical_count = self.asset_repo.count_orphan_critical_assets(company_id)
        bia_stats = self.asset_repo.bia_coverage_stats(company_id)
        total_relationships = self.ci_repo.count_all(company_id)
        relationships_by_type = self.ci_repo.count_by_type(company_id)
        most_depended_raw = self.ci_repo.count_incoming_by_asset(company_id)
        overdue_raw = self.asset_repo.find_overdue_bia_reviews(company_id, months=6)

        most_depended_upon = [
            MostDependedAssetDto(
                asset_id=m["asset_id"],
                asset_name=m["asset_name"],
                asset_tag=m.get("asset_tag"),
                incoming_count=m["count"],
            )
            for m in most_depended_raw
        ]

        overdue_bia_reviews = [
            OverdueBIAReviewDto(
                asset_id=o["id"],
                asset_name=o["name"],
                asset_tag=o.get("asset_tag"),
                criticality=o["criticality"],
                bia_reviewed_at=o.get("bia_reviewed_at"),
            )
            for o in overdue_raw
        ]

        return CMDBDashboardDto(
            criticality_distribution=criticality_distribution,
            orphan_critical_count=orphan_critical_count,
            bia_total_critical_high=bia_stats["total_critical_high"],
            bia_has_coverage=bia_stats["has_bia"],
            bia_coverage_pct=bia_stats["coverage_pct"],
            total_relationships=total_relationships,
            relationships_by_type=relationships_by_type,
            most_depended_upon=most_depended_upon,
            overdue_bia_reviews=overdue_bia_reviews,
        )
