from datetime import date

import pytest

from src.procurement_bc.vendor.domain.entities import (
    VendorRiskAssessment,
    calculate_vendor_risk_level,
)
from src.procurement_bc.vendor.domain.enums import VendorRiskLevel
from src.procurement_bc.vendor.domain.exceptions import (
    InvalidAssessmentScoreError,
)


class TestVendorRiskAssessmentCreate:
    def test_create_valid_assessment(self):
        assessment = VendorRiskAssessment.create(
            vendor_id="vendor1",
            company_id="company1",
            assessed_by="user1",
            assessment_date=date(2026, 2, 26),
            data_handling_score=2,
            security_certs_score=2,
            incident_response_score=2,
            business_continuity_score=2,
            subcontractor_score=2,
        )
        assert assessment.vendor_id == "vendor1"
        assert assessment.overall_risk_level == VendorRiskLevel.LOW
        assert assessment.is_deleted is False

    def test_create_with_optional_fields(self):
        assessment = VendorRiskAssessment.create(
            vendor_id="vendor1",
            company_id="company1",
            assessed_by="user1",
            assessment_date=date(2026, 2, 26),
            data_handling_score=3,
            security_certs_score=3,
            incident_response_score=3,
            business_continuity_score=3,
            subcontractor_score=3,
            next_review_date=date(2026, 8, 26),
            justification="Annual review",
        )
        assert assessment.next_review_date == date(2026, 8, 26)
        assert assessment.justification == "Annual review"

    def test_create_rejects_score_below_1(self):
        with pytest.raises(InvalidAssessmentScoreError):
            VendorRiskAssessment.create(
                vendor_id="v1",
                company_id="c1",
                assessed_by="u1",
                assessment_date=date(2026, 1, 1),
                data_handling_score=0,
                security_certs_score=3,
                incident_response_score=3,
                business_continuity_score=3,
                subcontractor_score=3,
            )

    def test_create_rejects_score_above_5(self):
        with pytest.raises(InvalidAssessmentScoreError):
            VendorRiskAssessment.create(
                vendor_id="v1",
                company_id="c1",
                assessed_by="u1",
                assessment_date=date(2026, 1, 1),
                data_handling_score=3,
                security_certs_score=6,
                incident_response_score=3,
                business_continuity_score=3,
                subcontractor_score=3,
            )

    def test_soft_delete(self):
        assessment = VendorRiskAssessment.create(
            vendor_id="v1",
            company_id="c1",
            assessed_by="u1",
            assessment_date=date(2026, 1, 1),
            data_handling_score=1,
            security_certs_score=1,
            incident_response_score=1,
            business_continuity_score=1,
            subcontractor_score=1,
        )
        assert assessment.is_deleted is False
        assessment.soft_delete()
        assert assessment.is_deleted is True


class TestCalculateRiskLevel:
    def test_all_ones_is_low(self):
        level = VendorRiskAssessment.calculate_risk_level([1, 1, 1, 1, 1])
        assert level == VendorRiskLevel.LOW

    def test_avg_2_0_is_low(self):
        level = VendorRiskAssessment.calculate_risk_level([2, 2, 2, 2, 2])
        assert level == VendorRiskLevel.LOW

    def test_avg_2_2_is_medium(self):
        # avg = (3+2+2+2+2)/5 = 2.2
        level = VendorRiskAssessment.calculate_risk_level([3, 2, 2, 2, 2])
        assert level == VendorRiskLevel.MEDIUM

    def test_avg_3_0_is_medium(self):
        level = VendorRiskAssessment.calculate_risk_level([3, 3, 3, 3, 3])
        assert level == VendorRiskLevel.MEDIUM

    def test_avg_3_2_is_high(self):
        # avg = (4+3+3+3+3)/5 = 3.2
        level = VendorRiskAssessment.calculate_risk_level([4, 3, 3, 3, 3])
        assert level == VendorRiskLevel.HIGH

    def test_avg_4_0_is_high(self):
        level = VendorRiskAssessment.calculate_risk_level([4, 4, 4, 4, 4])
        assert level == VendorRiskLevel.HIGH

    def test_avg_4_2_is_critical(self):
        # avg = (5+4+4+4+4)/5 = 4.2
        level = VendorRiskAssessment.calculate_risk_level([5, 4, 4, 4, 4])
        assert level == VendorRiskLevel.CRITICAL

    def test_all_fives_is_critical(self):
        level = VendorRiskAssessment.calculate_risk_level([5, 5, 5, 5, 5])
        assert level == VendorRiskLevel.CRITICAL


class TestCalculateVendorRiskLevel:
    def test_normal_vendor_returns_assessment_level(self):
        result = calculate_vendor_risk_level(
            VendorRiskLevel.MEDIUM, is_critical_ict=False, has_security_clauses=False,
        )
        assert result == VendorRiskLevel.MEDIUM

    def test_critical_ict_with_clauses_returns_assessment_level(self):
        result = calculate_vendor_risk_level(
            VendorRiskLevel.LOW, is_critical_ict=True, has_security_clauses=True,
        )
        assert result == VendorRiskLevel.LOW

    def test_critical_ict_without_clauses_escalates_to_critical(self):
        result = calculate_vendor_risk_level(
            VendorRiskLevel.LOW, is_critical_ict=True, has_security_clauses=False,
        )
        assert result == VendorRiskLevel.CRITICAL

    def test_critical_ict_without_clauses_already_critical(self):
        result = calculate_vendor_risk_level(
            VendorRiskLevel.CRITICAL, is_critical_ict=True, has_security_clauses=False,
        )
        assert result == VendorRiskLevel.CRITICAL
