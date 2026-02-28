from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.domain.enums import ContractStatus, VendorRiskLevel
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
)


@dataclass
class ExpiringContractDto:
    contract_id: str
    vendor_id: str
    vendor_name: str
    title: str
    end_date: date
    days_remaining: int


@dataclass
class ConcentrationRiskSummaryDto:
    vendor_id: str
    vendor_name: str
    critical_count: int
    total_critical: int
    percentage: float
    is_above_threshold: bool


@dataclass
class SupplyChainDashboardDto:
    total_vendors: int
    active_vendors: int
    vendors_by_risk_level: dict[str, int]
    critical_ict_count: int
    expiring_contracts_30: int
    expiring_contracts_60: int
    expiring_contracts_90: int
    expiring_contracts: list[ExpiringContractDto]
    concentration_risk_items: list[ConcentrationRiskSummaryDto]
    stale_assessment_count: int


@dataclass
class SupplyChainDashboardQuery(Query):
    company_id: str


class SupplyChainDashboardQueryHandler(
    QueryHandler[SupplyChainDashboardQuery, SupplyChainDashboardDto],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        contract_repo: VendorContractRepositoryInterface,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.vendor_repo = vendor_repo
        self.contract_repo = contract_repo
        self.assessment_repo = assessment_repo
        self.dependency_repo = dependency_repo

    def handle(
        self, query: SupplyChainDashboardQuery,
    ) -> SupplyChainDashboardDto:
        today = date.today()

        # Vendor counts
        all_vendors, total_vendors = self.vendor_repo.find_all(
            query.company_id, page=1, page_size=10000,
        )
        active_vendors = sum(1 for v in all_vendors if v.is_active)
        critical_ict_count = sum(
            1 for v in all_vendors if v.is_critical_ict and v.is_active
        )

        # Vendors by risk level
        risk_counts: dict[str, int] = {
            level.value: 0 for level in VendorRiskLevel
        }
        for v in all_vendors:
            if v.risk_level and v.is_active:
                risk_counts[v.risk_level.value] += 1

        # Expiring contracts (next 90 days)
        expiring_contracts: list[ExpiringContractDto] = []
        expiring_30 = 0
        expiring_60 = 0
        expiring_90 = 0

        vendor_map = {v.id: v.name for v in all_vendors}

        for v in all_vendors:
            contracts, _ = self.contract_repo.find_all_by_vendor(
                v.id, query.company_id,
                page=1, page_size=1000,
                status=ContractStatus.ACTIVE,
            )
            for c in contracts:
                if c.end_date and c.end_date >= today:
                    days_remaining = (c.end_date - today).days
                    if days_remaining <= 90:
                        expiring_contracts.append(
                            ExpiringContractDto(
                                contract_id=c.id,
                                vendor_id=c.vendor_id,
                                vendor_name=vendor_map.get(c.vendor_id, ""),
                                title=c.title,
                                end_date=c.end_date,
                                days_remaining=days_remaining,
                            )
                        )
                        if days_remaining <= 30:
                            expiring_30 += 1
                        if days_remaining <= 60:
                            expiring_60 += 1
                        expiring_90 += 1

        expiring_contracts.sort(key=lambda x: x.days_remaining)

        # Concentration risk
        from src.procurement_bc.vendor.application.queries.concentration_risk import (
            CONCENTRATION_THRESHOLD,
            ConcentrationRiskQueryHandler,
        )
        conc_handler = ConcentrationRiskQueryHandler(
            dependency_repo=self.dependency_repo,
            vendor_repo=self.vendor_repo,
        )
        from src.procurement_bc.vendor.application.queries.concentration_risk import (
            ConcentrationRiskQuery,
        )
        conc_items = conc_handler.handle(
            ConcentrationRiskQuery(company_id=query.company_id),
        )
        concentration_risk = [
            ConcentrationRiskSummaryDto(
                vendor_id=item.vendor_id,
                vendor_name=item.vendor_name,
                critical_count=item.critical_count,
                total_critical=item.total_critical,
                percentage=item.percentage,
                is_above_threshold=item.is_above_threshold,
            )
            for item in conc_items
        ]

        # Stale assessments
        stale_vendor_ids = self.assessment_repo.find_vendors_with_stale_assessments(
            query.company_id, as_of=today,
        )

        return SupplyChainDashboardDto(
            total_vendors=total_vendors,
            active_vendors=active_vendors,
            vendors_by_risk_level=risk_counts,
            critical_ict_count=critical_ict_count,
            expiring_contracts_30=expiring_30,
            expiring_contracts_60=expiring_60,
            expiring_contracts_90=expiring_90,
            expiring_contracts=expiring_contracts,
            concentration_risk_items=concentration_risk,
            stale_assessment_count=len(stale_vendor_ids),
        )
