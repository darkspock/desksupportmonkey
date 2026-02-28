from datetime import date
from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.commands.create_assessment import (
    CreateAssessmentCommand,
    CreateAssessmentCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_assessment import (
    SoftDeleteAssessmentCommand,
    SoftDeleteAssessmentCommandHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
    VendorRiskAssessment,
)
from src.procurement_bc.vendor.domain.enums import VendorRiskLevel
from src.procurement_bc.vendor.domain.exceptions import (
    AssessmentNotFoundError,
    VendorNotFoundError,
)


class TestCreateAssessmentCommandHandler:
    def setup_method(self):
        self.vendor_repo = MagicMock()
        self.assessment_repo = MagicMock()
        self.contract_repo = MagicMock()
        self.handler = CreateAssessmentCommandHandler(
            vendor_repo=self.vendor_repo,
            assessment_repo=self.assessment_repo,
            contract_repo=self.contract_repo,
        )

    def test_creates_assessment_and_caches_risk_level(self):
        vendor = Vendor(
            id="v1", company_id="c1", name="TestVendor",
            is_critical_ict=False,
        )
        self.vendor_repo.find_by_id.return_value = vendor
        self.contract_repo.has_active_contract_with_security_clauses.return_value = False

        self.handler.handle(
            CreateAssessmentCommand(
                vendor_id="v1",
                company_id="c1",
                assessed_by="u1",
                assessment_date=date(2026, 2, 26),
                data_handling_score=2,
                security_certs_score=2,
                incident_response_score=2,
                business_continuity_score=2,
                subcontractor_score=2,
            )
        )

        self.assessment_repo.save.assert_called_once()
        saved_assessment = self.assessment_repo.save.call_args[0][0]
        assert saved_assessment.overall_risk_level == VendorRiskLevel.LOW

        self.vendor_repo.save.assert_called_once()
        assert vendor.risk_level == VendorRiskLevel.LOW

    def test_escalates_critical_ict_without_clauses(self):
        vendor = Vendor(
            id="v1", company_id="c1", name="TestVendor",
            is_critical_ict=True,
        )
        self.vendor_repo.find_by_id.return_value = vendor
        self.contract_repo.has_active_contract_with_security_clauses.return_value = False

        self.handler.handle(
            CreateAssessmentCommand(
                vendor_id="v1",
                company_id="c1",
                assessed_by="u1",
                assessment_date=date(2026, 2, 26),
                data_handling_score=1,
                security_certs_score=1,
                incident_response_score=1,
                business_continuity_score=1,
                subcontractor_score=1,
            )
        )

        assert vendor.risk_level == VendorRiskLevel.CRITICAL

    def test_critical_ict_with_clauses_no_escalation(self):
        vendor = Vendor(
            id="v1", company_id="c1", name="TestVendor",
            is_critical_ict=True,
        )
        self.vendor_repo.find_by_id.return_value = vendor
        self.contract_repo.has_active_contract_with_security_clauses.return_value = True

        self.handler.handle(
            CreateAssessmentCommand(
                vendor_id="v1",
                company_id="c1",
                assessed_by="u1",
                assessment_date=date(2026, 2, 26),
                data_handling_score=1,
                security_certs_score=1,
                incident_response_score=1,
                business_continuity_score=1,
                subcontractor_score=1,
            )
        )

        assert vendor.risk_level == VendorRiskLevel.LOW

    def test_raises_vendor_not_found(self):
        self.vendor_repo.find_by_id.return_value = None

        with pytest.raises(VendorNotFoundError):
            self.handler.handle(
                CreateAssessmentCommand(
                    vendor_id="v1",
                    company_id="c1",
                    assessed_by="u1",
                    assessment_date=date(2026, 2, 26),
                    data_handling_score=3,
                    security_certs_score=3,
                    incident_response_score=3,
                    business_continuity_score=3,
                    subcontractor_score=3,
                )
            )


class TestSoftDeleteAssessmentCommandHandler:
    def setup_method(self):
        self.vendor_repo = MagicMock()
        self.assessment_repo = MagicMock()
        self.contract_repo = MagicMock()
        self.handler = SoftDeleteAssessmentCommandHandler(
            vendor_repo=self.vendor_repo,
            assessment_repo=self.assessment_repo,
            contract_repo=self.contract_repo,
        )

    def test_deletes_and_recalculates_from_latest(self):
        assessment = VendorRiskAssessment.create(
            id="a1", vendor_id="v1", company_id="c1",
            assessed_by="u1", assessment_date=date(2026, 2, 26),
            data_handling_score=4, security_certs_score=4,
            incident_response_score=4, business_continuity_score=4,
            subcontractor_score=4,
        )
        vendor = Vendor(
            id="v1", company_id="c1", name="TestVendor",
            risk_level=VendorRiskLevel.HIGH,
            is_critical_ict=False,
        )
        latest = VendorRiskAssessment.create(
            id="a2", vendor_id="v1", company_id="c1",
            assessed_by="u1", assessment_date=date(2026, 1, 1),
            data_handling_score=2, security_certs_score=2,
            incident_response_score=2, business_continuity_score=2,
            subcontractor_score=2,
        )
        self.assessment_repo.find_by_id.return_value = assessment
        self.vendor_repo.find_by_id.return_value = vendor
        self.assessment_repo.find_latest_by_vendor.return_value = latest
        self.contract_repo.has_active_contract_with_security_clauses.return_value = False

        self.handler.handle(
            SoftDeleteAssessmentCommand(
                assessment_id="a1", vendor_id="v1", company_id="c1",
            )
        )

        self.assessment_repo.soft_delete.assert_called_once_with(
            "a1", "v1", "c1",
        )
        assert vendor.risk_level == VendorRiskLevel.LOW

    def test_deletes_last_assessment_sets_risk_level_null(self):
        assessment = VendorRiskAssessment.create(
            id="a1", vendor_id="v1", company_id="c1",
            assessed_by="u1", assessment_date=date(2026, 2, 26),
            data_handling_score=3, security_certs_score=3,
            incident_response_score=3, business_continuity_score=3,
            subcontractor_score=3,
        )
        vendor = Vendor(
            id="v1", company_id="c1", name="TestVendor",
            risk_level=VendorRiskLevel.MEDIUM,
        )
        self.assessment_repo.find_by_id.return_value = assessment
        self.vendor_repo.find_by_id.return_value = vendor
        self.assessment_repo.find_latest_by_vendor.return_value = None

        self.handler.handle(
            SoftDeleteAssessmentCommand(
                assessment_id="a1", vendor_id="v1", company_id="c1",
            )
        )

        assert vendor.risk_level is None

    def test_raises_assessment_not_found(self):
        self.assessment_repo.find_by_id.return_value = None

        with pytest.raises(AssessmentNotFoundError):
            self.handler.handle(
                SoftDeleteAssessmentCommand(
                    assessment_id="a1", vendor_id="v1", company_id="c1",
                )
            )
