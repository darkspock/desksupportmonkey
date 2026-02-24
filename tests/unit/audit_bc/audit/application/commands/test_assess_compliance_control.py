"""Unit tests for AssessComplianceControlHandler."""
from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.assess_compliance_control import (
    AssessComplianceControlCommand,
    AssessComplianceControlHandler,
)
from src.audit_bc.audit.domain.entities import (
    ComplianceAssessment,
    ComplianceControl,
)
from src.audit_bc.audit.domain.enums import ComplianceStatus
from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    InvalidComplianceStatusError,
)


def _make_handler():
    repo = MagicMock()
    handler = AssessComplianceControlHandler(repo=repo)
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


class TestAssessComplianceControlHandler:

    def test_creates_new_assessment(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()
        repo.find_assessment.return_value = None

        handler.handle(
            AssessComplianceControlCommand(
                company_id="c1",
                control_id="ctrl1",
                status="compliant",
                assessed_by="user1",
                notes="All good",
            )
        )

        repo.save_assessment.assert_called_once()
        saved = repo.save_assessment.call_args[0][0]
        assert isinstance(saved, ComplianceAssessment)
        assert saved.status == ComplianceStatus.COMPLIANT
        assert saved.notes == "All good"
        assert saved.assessed_by == "user1"

    def test_updates_existing_assessment(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()
        existing = ComplianceAssessment.create(
            company_id="c1",
            control_id="ctrl1",
            status=ComplianceStatus.NOT_ASSESSED,
            assessed_by="user1",
        )
        repo.find_assessment.return_value = existing

        handler.handle(
            AssessComplianceControlCommand(
                company_id="c1",
                control_id="ctrl1",
                status="partial",
                assessed_by="user2",
                notes="Partially done",
            )
        )

        repo.save_assessment.assert_called_once()
        saved = repo.save_assessment.call_args[0][0]
        assert saved.status == ComplianceStatus.PARTIAL
        assert saved.notes == "Partially done"
        assert saved.assessed_by == "user2"
        assert saved.id == existing.id

    def test_raises_when_control_not_found(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = None

        with pytest.raises(ControlNotFoundError):
            handler.handle(
                AssessComplianceControlCommand(
                    company_id="c1",
                    control_id="nonexistent",
                    status="compliant",
                    assessed_by="user1",
                )
            )

        repo.save_assessment.assert_not_called()

    def test_raises_on_invalid_status(self):
        handler, repo = _make_handler()
        repo.find_control_by_id.return_value = _make_control()

        with pytest.raises(InvalidComplianceStatusError):
            handler.handle(
                AssessComplianceControlCommand(
                    company_id="c1",
                    control_id="ctrl1",
                    status="invalid_status",
                    assessed_by="user1",
                )
            )

        repo.save_assessment.assert_not_called()

    def test_all_valid_statuses_accepted(self):
        for status_val in ["compliant", "partial", "non_compliant", "not_assessed"]:
            handler, repo = _make_handler()
            repo.find_control_by_id.return_value = _make_control()
            repo.find_assessment.return_value = None

            handler.handle(
                AssessComplianceControlCommand(
                    company_id="c1",
                    control_id="ctrl1",
                    status=status_val,
                    assessed_by="user1",
                )
            )

            repo.save_assessment.assert_called_once()
