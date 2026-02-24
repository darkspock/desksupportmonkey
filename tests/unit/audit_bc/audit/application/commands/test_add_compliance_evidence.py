"""Unit tests for AddComplianceEvidenceHandler."""
from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.add_compliance_evidence import (
    AddComplianceEvidenceCommand,
    AddComplianceEvidenceHandler,
)
from src.audit_bc.audit.domain.entities import (
    ComplianceControl,
    ComplianceEvidence,
)
from src.audit_bc.audit.domain.enums import EvidenceType
from src.audit_bc.audit.domain.exceptions import ControlNotFoundError


def _make_handler():
    repo = MagicMock()
    handler = AddComplianceEvidenceHandler(repo=repo)
    return handler, repo


def _make_control(**overrides):
    defaults = dict(
        company_id="c1",
        code="NIS2-001",
        name="Test Control",
        framework="NIS2",
    )
    defaults.update(overrides)
    return ComplianceControl.create(**defaults)


class TestAddComplianceEvidenceHandler:

    def test_adds_evidence_successfully(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()

        handler.handle(
            AddComplianceEvidenceCommand(
                company_id="c1",
                control_id="ctrl1",
                evidence_type="manual",
                title="SOC2 Report",
                added_by="user1",
                description="Annual report",
                url="https://example.com/soc2.pdf",
            )
        )

        repo.save_evidence.assert_called_once()
        saved = repo.save_evidence.call_args[0][0]
        assert isinstance(saved, ComplianceEvidence)
        assert saved.evidence_type == EvidenceType.MANUAL
        assert saved.title == "SOC2 Report"
        assert saved.description == "Annual report"
        assert saved.url == "https://example.com/soc2.pdf"

    def test_adds_evidence_with_reference_id(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()

        handler.handle(
            AddComplianceEvidenceCommand(
                company_id="c1",
                control_id="ctrl1",
                evidence_type="incident",
                title="Incident reference",
                added_by="user1",
                reference_id="01INCIDENT000000000000000001",
            )
        )

        repo.save_evidence.assert_called_once()
        saved = repo.save_evidence.call_args[0][0]
        assert saved.evidence_type == EvidenceType.INCIDENT
        assert saved.reference_id == "01INCIDENT000000000000000001"

    def test_raises_when_control_not_found(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = None

        with pytest.raises(ControlNotFoundError):
            handler.handle(
                AddComplianceEvidenceCommand(
                    company_id="c1",
                    control_id="nonexistent",
                    evidence_type="manual",
                    title="Some evidence",
                    added_by="user1",
                )
            )

        repo.save_evidence.assert_not_called()

    def test_raises_on_invalid_evidence_type(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()

        with pytest.raises(ValueError):
            handler.handle(
                AddComplianceEvidenceCommand(
                    company_id="c1",
                    control_id="ctrl1",
                    evidence_type="invalid_type",
                    title="Some evidence",
                    added_by="user1",
                )
            )

        repo.save_evidence.assert_not_called()

    def test_all_valid_evidence_types_accepted(self):
        for etype in ["audit_log", "incident", "risk", "sla", "manual"]:
            handler, repo = _make_handler()
            repo.find_control_by_id.return_value = _make_control()

            handler.handle(
                AddComplianceEvidenceCommand(
                    company_id="c1",
                    control_id="ctrl1",
                    evidence_type=etype,
                    title=f"Evidence {etype}",
                    added_by="user1",
                )
            )

            repo.save_evidence.assert_called_once()

    def test_adds_evidence_with_minimal_fields(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()

        handler.handle(
            AddComplianceEvidenceCommand(
                company_id="c1",
                control_id="ctrl1",
                evidence_type="audit_log",
                title="Log entry",
                added_by="user1",
            )
        )

        repo.save_evidence.assert_called_once()
        saved = repo.save_evidence.call_args[0][0]
        assert saved.reference_id is None
        assert saved.description is None
        assert saved.url is None
