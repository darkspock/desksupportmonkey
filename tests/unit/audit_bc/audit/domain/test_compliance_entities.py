"""Unit tests for ComplianceAssessment and ComplianceEvidence entities."""
from datetime import datetime, timezone

import pytest

from src.audit_bc.audit.domain.entities import (
    ComplianceAssessment,
    ComplianceEvidence,
)
from src.audit_bc.audit.domain.enums import ComplianceStatus, EvidenceType


class TestComplianceAssessmentCreate:

    def test_create_assessment(self):
        assessment = ComplianceAssessment.create(
            company_id="01COMPANY000000000000000001",
            control_id="01CONTROL000000000000000001",
            status=ComplianceStatus.COMPLIANT,
            assessed_by="01USER0000000000000000000001",
            notes="Fully compliant after audit",
        )

        assert assessment.id is not None
        assert len(assessment.id) == 26
        assert assessment.company_id == "01COMPANY000000000000000001"
        assert assessment.control_id == "01CONTROL000000000000000001"
        assert assessment.status == ComplianceStatus.COMPLIANT
        assert assessment.notes == "Fully compliant after audit"
        assert assessment.assessed_by == "01USER0000000000000000000001"
        assert assessment.assessed_at is not None
        assert assessment.created_at is not None
        assert assessment.updated_at is not None

    def test_create_assessment_without_notes(self):
        assessment = ComplianceAssessment.create(
            company_id="01COMPANY000000000000000001",
            control_id="01CONTROL000000000000000001",
            status=ComplianceStatus.NOT_ASSESSED,
            assessed_by="01USER0000000000000000000001",
        )

        assert assessment.notes is None
        assert assessment.status == ComplianceStatus.NOT_ASSESSED

    def test_create_assessment_all_statuses(self):
        for status in ComplianceStatus:
            assessment = ComplianceAssessment.create(
                company_id="c1",
                control_id="ctrl1",
                status=status,
                assessed_by="u1",
            )
            assert assessment.status == status


class TestComplianceAssessmentUpdateStatus:

    def _make_assessment(self) -> ComplianceAssessment:
        return ComplianceAssessment.create(
            company_id="01COMPANY000000000000000001",
            control_id="01CONTROL000000000000000001",
            status=ComplianceStatus.NOT_ASSESSED,
            assessed_by="01USER0000000000000000000001",
        )

    def test_update_status(self):
        assessment = self._make_assessment()
        original_created_at = assessment.created_at

        assessment.update_status(
            status=ComplianceStatus.COMPLIANT,
            notes="Now compliant",
            assessed_by="01USER0000000000000000000002",
        )

        assert assessment.status == ComplianceStatus.COMPLIANT
        assert assessment.notes == "Now compliant"
        assert assessment.assessed_by == "01USER0000000000000000000002"
        assert assessment.assessed_at is not None
        assert assessment.updated_at is not None
        assert assessment.created_at == original_created_at

    def test_update_status_clears_notes_when_none(self):
        assessment = self._make_assessment()
        assessment.update_status(
            status=ComplianceStatus.PARTIAL,
            notes="Has notes",
            assessed_by="u1",
        )
        assert assessment.notes == "Has notes"

        assessment.update_status(
            status=ComplianceStatus.NON_COMPLIANT,
            notes=None,
            assessed_by="u2",
        )
        assert assessment.notes is None

    def test_update_status_changes_assessed_at(self):
        assessment = self._make_assessment()
        first_assessed_at = assessment.assessed_at

        assessment.update_status(
            status=ComplianceStatus.COMPLIANT,
            notes=None,
            assessed_by="u1",
        )

        assert assessment.assessed_at >= first_assessed_at


class TestComplianceEvidenceCreate:

    def test_create_evidence(self):
        evidence = ComplianceEvidence.create(
            company_id="01COMPANY000000000000000001",
            control_id="01CONTROL000000000000000001",
            evidence_type=EvidenceType.MANUAL,
            title="SOC2 Report",
            added_by="01USER0000000000000000000001",
            reference_id=None,
            description="Annual SOC2 Type II report",
            url="https://example.com/soc2.pdf",
        )

        assert evidence.id is not None
        assert len(evidence.id) == 26
        assert evidence.company_id == "01COMPANY000000000000000001"
        assert evidence.control_id == "01CONTROL000000000000000001"
        assert evidence.evidence_type == EvidenceType.MANUAL
        assert evidence.title == "SOC2 Report"
        assert evidence.added_by == "01USER0000000000000000000001"
        assert evidence.reference_id is None
        assert evidence.description == "Annual SOC2 Type II report"
        assert evidence.url == "https://example.com/soc2.pdf"
        assert evidence.created_at is not None

    def test_create_evidence_with_reference_id(self):
        evidence = ComplianceEvidence.create(
            company_id="c1",
            control_id="ctrl1",
            evidence_type=EvidenceType.INCIDENT,
            title="Incident INC-001",
            added_by="u1",
            reference_id="01INCIDENT000000000000000001",
        )

        assert evidence.reference_id == "01INCIDENT000000000000000001"
        assert evidence.evidence_type == EvidenceType.INCIDENT

    def test_create_evidence_minimal(self):
        evidence = ComplianceEvidence.create(
            company_id="c1",
            control_id="ctrl1",
            evidence_type=EvidenceType.AUDIT_LOG,
            title="Log evidence",
            added_by="u1",
        )

        assert evidence.reference_id is None
        assert evidence.description is None
        assert evidence.url is None

    def test_create_evidence_all_types(self):
        for etype in EvidenceType:
            evidence = ComplianceEvidence.create(
                company_id="c1",
                control_id="ctrl1",
                evidence_type=etype,
                title=f"Evidence for {etype.value}",
                added_by="u1",
            )
            assert evidence.evidence_type == etype
