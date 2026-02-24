"""Unit tests for RemoveComplianceEvidenceHandler."""
from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.remove_compliance_evidence import (
    RemoveComplianceEvidenceCommand,
    RemoveComplianceEvidenceHandler,
)
from src.audit_bc.audit.domain.entities import ComplianceEvidence
from src.audit_bc.audit.domain.enums import EvidenceType
from src.audit_bc.audit.domain.exceptions import EvidenceNotFoundError


def _make_handler():
    repo = MagicMock()
    handler = RemoveComplianceEvidenceHandler(repo=repo)
    return handler, repo


def _make_evidence(**overrides):
    defaults = dict(
        company_id="c1",
        control_id="ctrl1",
        evidence_type=EvidenceType.MANUAL,
        title="Test Evidence",
        added_by="user1",
    )
    defaults.update(overrides)
    return ComplianceEvidence.create(**defaults)


class TestRemoveComplianceEvidenceHandler:

    def test_removes_evidence_successfully(self):
        handler, repo = _make_handler()
        evidence = _make_evidence()
        repo.find_evidence_by_id.return_value = evidence

        handler.handle(
            RemoveComplianceEvidenceCommand(
                evidence_id=evidence.id,
                company_id="c1",
            )
        )

        repo.delete_evidence.assert_called_once_with(evidence.id)

    def test_raises_when_evidence_not_found(self):
        handler, repo = _make_handler()
        repo.find_evidence_by_id.return_value = None

        with pytest.raises(EvidenceNotFoundError):
            handler.handle(
                RemoveComplianceEvidenceCommand(
                    evidence_id="nonexistent",
                    company_id="c1",
                )
            )

        repo.delete_evidence.assert_not_called()

    def test_passes_company_id_for_isolation(self):
        handler, repo = _make_handler()
        evidence = _make_evidence()
        repo.find_evidence_by_id.return_value = evidence

        handler.handle(
            RemoveComplianceEvidenceCommand(
                evidence_id=evidence.id,
                company_id="c1",
            )
        )

        repo.find_evidence_by_id.assert_called_once_with(
            evidence.id, "c1"
        )
