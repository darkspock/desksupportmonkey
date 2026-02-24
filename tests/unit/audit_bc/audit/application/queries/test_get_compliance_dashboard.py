"""Unit tests for GetComplianceDashboardQueryHandler."""
from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.queries.get_compliance_dashboard import (
    GetComplianceDashboardQuery,
    GetComplianceDashboardQueryHandler,
)
from src.audit_bc.audit.domain.entities import (
    ComplianceAssessment,
    ComplianceControl,
)
from src.audit_bc.audit.domain.enums import ComplianceStatus


def _make_handler(controls=None, assessments=None, evidence_counts=None):
    repo = MagicMock()
    repo.find_controls.return_value = controls or []
    repo.find_assessments_by_company.return_value = assessments or []
    repo.count_evidence_by_control.return_value = evidence_counts or {}
    handler = GetComplianceDashboardQueryHandler(repo=repo)
    return handler, repo


def _make_control(control_id="ctrl1", **overrides):
    defaults = dict(
        company_id="c1",
        code="NIS2-001",
        name="Test Control",
        framework="NIS2",
    )
    defaults.update(overrides)
    ctrl = ComplianceControl.create(**defaults)
    ctrl.id = control_id
    return ctrl


def _make_assessment(control_id="ctrl1", status=ComplianceStatus.COMPLIANT, **overrides):
    defaults = dict(
        company_id="c1",
        control_id=control_id,
        status=status,
        assessed_by="user1",
    )
    defaults.update(overrides)
    return ComplianceAssessment.create(**defaults)


class TestGetComplianceDashboardQueryHandler:

    def test_empty_controls(self):
        handler, repo = _make_handler()

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        assert result.total_controls == 0
        assert result.overall_compliance_pct == 0.0
        assert result.compliant == 0
        assert result.frameworks == []
        assert result.gap_controls == []

    def test_all_compliant(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
            _make_control("c2", code="NIS2-002", framework="NIS2"),
        ]
        assessments = [
            _make_assessment("c1", ComplianceStatus.COMPLIANT),
            _make_assessment("c2", ComplianceStatus.COMPLIANT),
        ]
        handler, repo = _make_handler(controls, assessments)

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        assert result.total_controls == 2
        assert result.compliant == 2
        assert result.overall_compliance_pct == 100.0
        assert result.gap_controls == []
        assert len(result.frameworks) == 1
        assert result.frameworks[0].framework == "NIS2"
        assert result.frameworks[0].compliance_pct == 100.0

    def test_mixed_statuses(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
            _make_control("c2", code="NIS2-002", framework="NIS2"),
            _make_control("c3", code="DORA-001", framework="DORA"),
            _make_control("c4", code="DORA-002", framework="DORA"),
        ]
        assessments = [
            _make_assessment("c1", ComplianceStatus.COMPLIANT),
            _make_assessment("c2", ComplianceStatus.PARTIAL),
            _make_assessment("c3", ComplianceStatus.NON_COMPLIANT),
            # c4 has no assessment -> NOT_ASSESSED
        ]
        handler, repo = _make_handler(controls, assessments)

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        assert result.total_controls == 4
        assert result.compliant == 1
        assert result.partial == 1
        assert result.non_compliant == 1
        assert result.not_assessed == 1
        assert result.overall_compliance_pct == 25.0
        assert len(result.gap_controls) == 2
        gap_statuses = {g.status for g in result.gap_controls}
        assert "non_compliant" in gap_statuses
        assert "not_assessed" in gap_statuses

    def test_framework_filter(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
            _make_control("c2", code="DORA-001", framework="DORA"),
        ]
        assessments = [
            _make_assessment("c1", ComplianceStatus.COMPLIANT),
            _make_assessment("c2", ComplianceStatus.NON_COMPLIANT),
        ]
        handler, repo = _make_handler(controls, assessments)

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1", framework="NIS2")
        )

        assert result.total_controls == 1
        assert result.compliant == 1
        assert result.non_compliant == 0
        assert result.overall_compliance_pct == 100.0
        assert len(result.frameworks) == 1
        assert result.frameworks[0].framework == "NIS2"

    def test_evidence_counts(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
            _make_control("c2", code="NIS2-002", framework="NIS2"),
        ]
        evidence_counts = {"c1": 3, "c2": 0}
        handler, repo = _make_handler(
            controls, evidence_counts=evidence_counts
        )

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        assert result.controls_with_evidence == 1
        assert result.controls_without_evidence == 1
        assert result.frameworks[0].evidence_coverage_pct == 50.0

    def test_controls_without_assessment_are_not_assessed(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
        ]
        handler, repo = _make_handler(controls, assessments=[])

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        assert result.not_assessed == 1
        assert result.compliant == 0
        assert len(result.gap_controls) == 1
        assert result.gap_controls[0].status == "not_assessed"

    def test_multiple_frameworks_sorted(self):
        controls = [
            _make_control("c1", code="NIS2-001", framework="NIS2"),
            _make_control("c2", code="DORA-001", framework="DORA"),
            _make_control("c3", code="ISO-001", framework="ISO 27001"),
        ]
        handler, repo = _make_handler(controls)

        result = handler.handle(
            GetComplianceDashboardQuery(company_id="c1")
        )

        fw_names = [f.framework for f in result.frameworks]
        assert fw_names == ["DORA", "ISO 27001", "NIS2"]
