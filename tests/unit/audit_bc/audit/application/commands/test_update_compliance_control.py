from unittest.mock import MagicMock

import pytest

from src.audit_bc.audit.application.commands.update_compliance_control import (
    UpdateComplianceControlCommand,
    UpdateComplianceControlHandler,
)
from src.audit_bc.audit.domain.entities import ComplianceControl
from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    PredefinedControlError,
)


class TestUpdateComplianceControlHandler:
    def _make_handler(self):
        repo = MagicMock()
        handler = UpdateComplianceControlHandler(repo=repo)
        return handler, repo

    def test_updates_custom_control(self):
        handler, repo = self._make_handler()
        control = ComplianceControl(
            id="ctrl1", company_id="c1", code="CUSTOM-001",
            name="Old Name", framework="CUSTOM", description=None,
            is_predefined=False, is_active=True,
        )
        repo.find_control_by_id.return_value = control

        handler.handle(
            UpdateComplianceControlCommand(
                control_id="ctrl1", company_id="c1",
                name="New Name", description="Updated desc",
            )
        )

        repo.save_control.assert_called_once()
        assert control.name == "New Name"
        assert control.description == "Updated desc"

    def test_rejects_predefined_control(self):
        handler, repo = self._make_handler()
        repo.find_control_by_id.return_value = ComplianceControl(
            id="ctrl1", company_id=None, code="NIS2-ART21-2A",
            name="Predefined", framework="NIS2", description=None,
            is_predefined=True, is_active=True,
        )

        with pytest.raises(PredefinedControlError):
            handler.handle(
                UpdateComplianceControlCommand(
                    control_id="ctrl1", company_id="c1", name="Changed",
                )
            )

    def test_rejects_not_found(self):
        handler, repo = self._make_handler()
        repo.find_control_by_id.return_value = None

        with pytest.raises(ControlNotFoundError):
            handler.handle(
                UpdateComplianceControlCommand(
                    control_id="missing", company_id="c1", name="X",
                )
            )
