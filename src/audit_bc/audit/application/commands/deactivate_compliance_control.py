from dataclasses import dataclass

from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    PredefinedControlError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class DeactivateComplianceControlCommand(Command):
    control_id: str
    company_id: str


class DeactivateComplianceControlHandler(
    CommandHandler[DeactivateComplianceControlCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: DeactivateComplianceControlCommand) -> None:
        control = self.repo.find_control_by_id(
            command.control_id, company_id=command.company_id
        )
        if control is None:
            raise ControlNotFoundError(
                f"Control {command.control_id} not found"
            )
        if control.is_predefined:
            raise PredefinedControlError(
                "Cannot deactivate predefined compliance controls"
            )

        control.is_active = False
        self.repo.save_control(control)
