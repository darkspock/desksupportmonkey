from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from src.procurement_bc.vendor.application.queries.get_assessment import (
    GetAssessmentQuery,
    GetAssessmentQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_assessments import (
    ListAssessmentsQuery,
    ListAssessmentsQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorRiskAssessment
from src.procurement_bc.vendor.domain.enums import VendorRiskLevel
from src.procurement_bc.vendor.domain.exceptions import AssessmentNotFoundError


def _make_assessment(**overrides):
    defaults = dict(
        id="a1",
        vendor_id="v1",
        company_id="c1",
        assessed_by="u1",
        assessment_date=date(2026, 2, 26),
        data_handling_score=3,
        security_certs_score=3,
        incident_response_score=3,
        business_continuity_score=3,
        subcontractor_score=3,
        overall_risk_level=VendorRiskLevel.MEDIUM,
        created_at=datetime(2026, 2, 26, 10, 0),
    )
    defaults.update(overrides)
    return VendorRiskAssessment(**defaults)


class TestListAssessmentsQueryHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = ListAssessmentsQueryHandler(
            assessment_repo=self.repo,
        )

    def test_returns_paginated_assessments(self):
        a1 = _make_assessment(id="a1")
        a2 = _make_assessment(id="a2")
        self.repo.find_all_by_vendor.return_value = ([a1, a2], 2)

        dtos, total = self.handler.handle(
            ListAssessmentsQuery(
                vendor_id="v1", company_id="c1",
                page=1, page_size=20,
            )
        )

        assert total == 2
        assert len(dtos) == 2
        assert dtos[0].id == "a1"
        assert dtos[0].overall_risk_level == "medium"

    def test_returns_empty_list(self):
        self.repo.find_all_by_vendor.return_value = ([], 0)

        dtos, total = self.handler.handle(
            ListAssessmentsQuery(
                vendor_id="v1", company_id="c1",
            )
        )

        assert total == 0
        assert dtos == []


class TestGetAssessmentQueryHandler:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = GetAssessmentQueryHandler(
            assessment_repo=self.repo,
        )

    def test_returns_assessment(self):
        assessment = _make_assessment()
        self.repo.find_by_id.return_value = assessment

        dto = self.handler.handle(
            GetAssessmentQuery(
                assessment_id="a1", vendor_id="v1", company_id="c1",
            )
        )

        assert dto.id == "a1"
        assert dto.overall_risk_level == "medium"
        assert dto.data_handling_score == 3

    def test_raises_not_found(self):
        self.repo.find_by_id.return_value = None

        with pytest.raises(AssessmentNotFoundError):
            self.handler.handle(
                GetAssessmentQuery(
                    assessment_id="x", vendor_id="v1", company_id="c1",
                )
            )
