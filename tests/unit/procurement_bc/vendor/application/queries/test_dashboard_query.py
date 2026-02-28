from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.queries.supply_chain_dashboard import (
    SupplyChainDashboardQuery,
    SupplyChainDashboardQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorContract,
    VendorDependency,
)
from src.procurement_bc.vendor.domain.enums import (
    BusinessFunction,
    ContractStatus,
    ContractType,
    VendorRiskLevel,
)

COMPANY = "comp01"


def _vendor(
    vid: str,
    risk_level: VendorRiskLevel | None = None,
    is_active: bool = True,
    is_critical_ict: bool = False,
) -> Vendor:
    return Vendor(
        id=vid,
        company_id=COMPANY,
        name=f"Vendor {vid}",
        is_active=is_active,
        is_critical_ict=is_critical_ict,
        risk_level=risk_level,
    )


def _contract(
    cid: str,
    vendor_id: str,
    end_date: date | None = None,
    status: ContractStatus = ContractStatus.ACTIVE,
) -> VendorContract:
    return VendorContract(
        id=cid,
        vendor_id=vendor_id,
        company_id=COMPANY,
        contract_type=ContractType.SERVICE,
        title=f"Contract {cid}",
        start_date=date(2025, 1, 1),
        status=status,
        end_date=end_date,
    )


def _make_handler():
    vendor_repo = MagicMock()
    contract_repo = MagicMock()
    assessment_repo = MagicMock()
    dependency_repo = MagicMock()
    return (
        SupplyChainDashboardQueryHandler(
            vendor_repo=vendor_repo,
            contract_repo=contract_repo,
            assessment_repo=assessment_repo,
            dependency_repo=dependency_repo,
        ),
        vendor_repo,
        contract_repo,
        assessment_repo,
        dependency_repo,
    )


class TestSupplyChainDashboardQuery:
    def test_empty_company(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        vendor_repo.find_all.return_value = ([], 0)
        dep_repo.find_all_critical_by_company.return_value = []
        assessment_repo.find_vendors_with_stale_assessments.return_value = []

        result = handler.handle(SupplyChainDashboardQuery(company_id=COMPANY))

        assert result.total_vendors == 0
        assert result.active_vendors == 0
        assert result.critical_ict_count == 0
        assert result.expiring_contracts_30 == 0
        assert result.expiring_contracts == []
        assert result.stale_assessment_count == 0

    def test_full_dashboard(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        today = date.today()

        vendors = [
            _vendor("v1", VendorRiskLevel.LOW, is_critical_ict=True),
            _vendor("v2", VendorRiskLevel.HIGH),
            _vendor("v3", VendorRiskLevel.CRITICAL),
            _vendor("v4", is_active=False),
        ]
        vendor_repo.find_all.return_value = (vendors, 4)

        # Contracts: v1 has one expiring in 20 days, v2 has one in 50 days
        c1 = _contract("c1", "v1", end_date=today + timedelta(days=20))
        c2 = _contract("c2", "v2", end_date=today + timedelta(days=50))

        def find_all_by_vendor(vid, cid, page, page_size, status=None):
            if vid == "v1":
                return ([c1], 1)
            if vid == "v2":
                return ([c2], 1)
            return ([], 0)

        contract_repo.find_all_by_vendor.side_effect = find_all_by_vendor

        dep_repo.find_all_critical_by_company.return_value = []
        assessment_repo.find_vendors_with_stale_assessments.return_value = [
            "v3",
        ]

        result = handler.handle(SupplyChainDashboardQuery(company_id=COMPANY))

        assert result.total_vendors == 4
        assert result.active_vendors == 3
        assert result.critical_ict_count == 1
        assert result.expiring_contracts_30 == 1  # c1 at 20 days
        assert result.expiring_contracts_60 == 2  # c1 + c2
        assert result.expiring_contracts_90 == 2
        assert len(result.expiring_contracts) == 2
        assert result.expiring_contracts[0].contract_id == "c1"
        assert result.vendors_by_risk_level["low"] == 1
        assert result.vendors_by_risk_level["high"] == 1
        assert result.vendors_by_risk_level["critical"] == 1
        assert result.stale_assessment_count == 1

    def test_no_expiring_contracts(self):
        handler, vendor_repo, contract_repo, assessment_repo, dep_repo = (
            _make_handler()
        )
        today = date.today()

        vendors = [_vendor("v1", VendorRiskLevel.LOW)]
        vendor_repo.find_all.return_value = (vendors, 1)

        # Contract ends in 120 days — not expiring within 90
        c1 = _contract("c1", "v1", end_date=today + timedelta(days=120))
        contract_repo.find_all_by_vendor.return_value = ([c1], 1)

        dep_repo.find_all_critical_by_company.return_value = []
        assessment_repo.find_vendors_with_stale_assessments.return_value = []

        result = handler.handle(SupplyChainDashboardQuery(company_id=COMPANY))

        assert result.expiring_contracts_30 == 0
        assert result.expiring_contracts_60 == 0
        assert result.expiring_contracts_90 == 0
        assert result.expiring_contracts == []
