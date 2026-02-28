from collections import Counter
from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.domain.repository import (
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
)

CONCENTRATION_THRESHOLD = 0.40


@dataclass
class ConcentrationRiskItem:
    vendor_id: str
    vendor_name: str
    critical_count: int
    total_critical: int
    percentage: float
    is_above_threshold: bool


@dataclass
class ConcentrationRiskQuery(Query):
    company_id: str


class ConcentrationRiskQueryHandler(
    QueryHandler[ConcentrationRiskQuery, list[ConcentrationRiskItem]],
):
    def __init__(
        self,
        dependency_repo: VendorDependencyRepositoryInterface,
        vendor_repo: VendorRepositoryInterface,
    ):
        self.dependency_repo = dependency_repo
        self.vendor_repo = vendor_repo

    def handle(
        self, query: ConcentrationRiskQuery,
    ) -> list[ConcentrationRiskItem]:
        critical_deps = self.dependency_repo.find_all_critical_by_company(
            query.company_id,
        )
        if not critical_deps:
            return []

        total_critical = len(critical_deps)
        vendor_counts: Counter[str] = Counter()
        for dep in critical_deps:
            vendor_counts[dep.vendor_id] += 1

        items = []
        for vendor_id, count in vendor_counts.most_common():
            percentage = count / total_critical
            vendor = self.vendor_repo.find_by_id(
                vendor_id, query.company_id,
            )
            vendor_name = vendor.name if vendor else "Unknown"
            items.append(
                ConcentrationRiskItem(
                    vendor_id=vendor_id,
                    vendor_name=vendor_name,
                    critical_count=count,
                    total_critical=total_critical,
                    percentage=round(percentage, 4),
                    is_above_threshold=percentage >= CONCENTRATION_THRESHOLD,
                )
            )
        return items
