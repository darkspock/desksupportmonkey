from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.create_compliance_control import (
    CreateComplianceControlCommand,
    CreateComplianceControlHandler,
)
from src.audit_bc.audit.domain.entities import ComplianceControl
from src.audit_bc.audit.domain.exceptions import ControlCodeExistsError


class TestCreateComplianceControlHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = CreateComplianceControlHandler(repo=repo)
        return handler, repo

    def test_creates_control_successfully(self):
        handler, repo = self._make_handler()
        repo.find_control_by_code.return_value = None

        handler.handle(
            CreateComplianceControlCommand(
                company_id="c1",
                code="CUSTOM-001",
                name="Custom",
                framework="CUSTOM",
                description="desc",
            )
        )

        repo.save_control.assert_called_once()
        saved = repo.save_control.call_args[0][0]
        assert isinstance(saved, ComplianceControl)
        assert saved.code == "CUSTOM-001"
        assert saved.company_id == "c1"
        assert saved.is_predefined is False

    def test_rejects_duplicate_code(self):
        handler, repo = self._make_handler()
        repo.find_control_by_code.return_value = ComplianceControl(
            id="existing",
            company_id="c1",
            code="CUSTOM-001",
            name="Existing",
            framework="CUSTOM",
            description=None,
            is_predefined=False,
            is_active=True,
        )

        with pytest.raises(ControlCodeExistsError):
            handler.handle(
                CreateComplianceControlCommand(
                    company_id="c1",
                    code="CUSTOM-001",
                    name="New",
                    framework="CUSTOM",
                )
            )

        repo.save_control.assert_not_called()
