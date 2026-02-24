from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.deactivate_compliance_control import (
    DeactivateComplianceControlCommand,
    DeactivateComplianceControlHandler,
)
from src.audit_bc.audit.domain.entities import ComplianceControl
from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    PredefinedControlError,
)


class TestDeactivateComplianceControlHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = DeactivateComplianceControlHandler(repo=repo)
        return handler, repo

    def test_deactivates_custom_control(self):
        handler, repo = self._make_handler()
        control = ComplianceControl(
            id="ctrl1", company_id="c1", code="CUSTOM-001",
            name="Custom", framework="CUSTOM", description=None,
            is_predefined=False, is_active=True,
        )
        repo.find_control_by_id.return_value = control

        handler.handle(
            DeactivateComplianceControlCommand(
                control_id="ctrl1", company_id="c1",
            )
        )

        repo.save_control.assert_called_once()
        assert control.is_active is False

    def test_rejects_predefined(self):
        handler, repo = self._make_handler()
        repo.find_control_by_id.return_value = ComplianceControl(
            id="ctrl1", company_id=None, code="NIS2-ART21-2A",
            name="Predefined", framework="NIS2", description=None,
            is_predefined=True, is_active=True,
        )

        with pytest.raises(PredefinedControlError):
            handler.handle(
                DeactivateComplianceControlCommand(
                    control_id="ctrl1", company_id="c1",
                )
            )

    def test_rejects_not_found(self):
        handler, repo = self._make_handler()
        repo.find_control_by_id.return_value = None

        with pytest.raises(ControlNotFoundError):
            handler.handle(
                DeactivateComplianceControlCommand(
                    control_id="missing", company_id="c1",
                )
            )
