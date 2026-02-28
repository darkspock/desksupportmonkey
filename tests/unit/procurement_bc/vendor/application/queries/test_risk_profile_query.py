from datetime import date
from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.ports import (
    IncidentSummary,
    RiskSummary,
)
from src.procurement_bc.vendor.application.queries.get_vendor_risk_profile import (
    GetVendorRiskProfileQuery,
    GetVendorRiskProfileQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorDependency,
    VendorRiskAssessment,
)
from src.procurement_bc.vendor.domain.enums import (
    BusinessFunction,
    ContractStatus,
    VendorCategory,
    VendorRiskLevel,
)
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError


@pytest.fixture
def vendor():
    v = Vendor.create(
        company_id="comp1",
        name="Acme Corp",
        id="vendor1",
    )
    v.is_critical_ict = True
    v.risk_level = VendorRiskLevel.HIGH
    v.category = VendorCategory.HARDWARE
    v.website = "https://acme.com"
    return v


@pytest.fixture
def assessment():
    return VendorRiskAssessment.create(
        vendor_id="vendor1",
        company_id="comp1",
        assessed_by="user1",
        assessment_date=date(2026, 1, 15),
        data_handling_score=3,
        security_certs_score=4,
        incident_response_score=3,
        business_continuity_score=4,
        subcontractor_score=3,
        next_review_date=date(2026, 7, 15),
        justification="Good overall",
        id="assess1",
    )


@pytest.fixture
def handler():
    vendor_repo = MagicMock()
    contract_repo = MagicMock()
    assessment_repo = MagicMock()
    dependency_repo = MagicMock()
    incident_reader = MagicMock()
    risk_reader = MagicMock()

    h = GetVendorRiskProfileQueryHandler(
        vendor_repo=vendor_repo,
        contract_repo=contract_repo,
        assessment_repo=assessment_repo,
        dependency_repo=dependency_repo,
        incident_reader=incident_reader,
        risk_reader=risk_reader,
    )
    return h


class TestGetVendorRiskProfileQueryHandler:

    def test_full_profile(self, handler, vendor, assessment):
        handler.vendor_repo.find_by_id.return_value = vendor
        handler.assessment_repo.find_latest_by_vendor.return_value = assessment

        # Active contracts
        handler.contract_repo.find_all_by_vendor.side_effect = [
            ([], 2),  # active contracts query
            ([], 5),  # total contracts query
        ]

        # Dependencies
        dep1 = VendorDependency.create(
            vendor_id="vendor1",
            company_id="comp1",
            service_description="Cloud hosting",
            business_function=BusinessFunction.CLOUD_INFRASTRUCTURE,
            is_critical=True,
            id="dep1",
        )
        dep2 = VendorDependency.create(
            vendor_id="vendor1",
            company_id="comp1",
            service_description="Email service",
            business_function=BusinessFunction.COMMUNICATIONS,
            is_critical=False,
            id="dep2",
        )
        handler.dependency_repo.find_all_by_vendor.return_value = (
            [dep1, dep2], 2,
        )

        # Cross-BC
        handler.incident_reader.find_by_vendor.return_value = (
            [
                IncidentSummary(
                    id="inc1", title="Data breach", severity="high",
                    status="detected", created_at=None,
                ),
            ],
            1,
        )
        handler.risk_reader.find_by_vendor.return_value = [
            RiskSummary(
                id="risk1", title="Supply risk",
                risk_level="high", status="open",
            ),
        ]

        result = handler.handle(
            GetVendorRiskProfileQuery(
                vendor_id="vendor1", company_id="comp1",
            )
        )

        assert result.id == "vendor1"
        assert result.name == "Acme Corp"
        assert result.is_critical_ict is True
        assert result.risk_level == "high"
        assert result.category == "hardware"
        assert result.website == "https://acme.com"
        assert result.latest_assessment is not None
        assert result.latest_assessment.overall_risk_level == "high"
        assert result.latest_assessment.data_handling_score == 3
        assert result.active_contracts_count == 2
        assert result.total_contracts_count == 5
        assert result.dependency_count == 2
        assert result.critical_dependency_count == 1
        assert result.incident_count == 1
        assert result.risk_count == 1
        assert len(result.incidents) == 1
        assert result.incidents[0].title == "Data breach"
        assert len(result.risks) == 1
        assert result.risks[0].title == "Supply risk"

    def test_vendor_not_found(self, handler):
        handler.vendor_repo.find_by_id.return_value = None

        with pytest.raises(VendorNotFoundError):
            handler.handle(
                GetVendorRiskProfileQuery(
                    vendor_id="missing", company_id="comp1",
                )
            )

    def test_no_assessment_no_incidents_no_risks(self, handler, vendor):
        handler.vendor_repo.find_by_id.return_value = vendor
        handler.assessment_repo.find_latest_by_vendor.return_value = None
        handler.contract_repo.find_all_by_vendor.side_effect = [
            ([], 0),
            ([], 0),
        ]
        handler.dependency_repo.find_all_by_vendor.return_value = ([], 0)
        handler.incident_reader.find_by_vendor.return_value = ([], 0)
        handler.risk_reader.find_by_vendor.return_value = []

        result = handler.handle(
            GetVendorRiskProfileQuery(
                vendor_id="vendor1", company_id="comp1",
            )
        )

        assert result.latest_assessment is None
        assert result.active_contracts_count == 0
        assert result.total_contracts_count == 0
        assert result.dependency_count == 0
        assert result.critical_dependency_count == 0
        assert result.incident_count == 0
        assert result.risk_count == 0
        assert result.incidents == []
        assert result.risks == []

    def test_multiple_critical_dependencies(self, handler, vendor):
        handler.vendor_repo.find_by_id.return_value = vendor
        handler.assessment_repo.find_latest_by_vendor.return_value = None
        handler.contract_repo.find_all_by_vendor.side_effect = [
            ([], 0), ([], 0),
        ]

        deps = [
            VendorDependency.create(
                vendor_id="vendor1",
                company_id="comp1",
                service_description=f"Service {i}",
                business_function=BusinessFunction.CLOUD_INFRASTRUCTURE,
                is_critical=(i < 3),
                id=f"dep{i}",
            )
            for i in range(5)
        ]
        handler.dependency_repo.find_all_by_vendor.return_value = (deps, 5)
        handler.incident_reader.find_by_vendor.return_value = ([], 0)
        handler.risk_reader.find_by_vendor.return_value = []

        result = handler.handle(
            GetVendorRiskProfileQuery(
                vendor_id="vendor1", company_id="comp1",
            )
        )

        assert result.dependency_count == 5
        assert result.critical_dependency_count == 3
