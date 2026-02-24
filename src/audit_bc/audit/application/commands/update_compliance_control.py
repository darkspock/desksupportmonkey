from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    PredefinedControlError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class UpdateComplianceControlCommand(Command):
    control_id: str
    company_id: str
    name: Optional[str] = None
    description: Optional[str] = None


class UpdateComplianceControlHandler(
    CommandHandler[UpdateComplianceControlCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: UpdateComplianceControlCommand) -> None:
        control = self.repo.find_control_by_id(
            command.control_id, company_id=command.company_id
        )
        if control is None:
            raise ControlNotFoundError(
                f"Control {command.control_id} not found"
            )
        if control.is_predefined:
            raise PredefinedControlError(
                "Cannot modify predefined compliance controls"
            )

        if command.name is not None:
            control.name = command.name
        if command.description is not None:
            control.description = command.description

        self.repo.save_control(control)
