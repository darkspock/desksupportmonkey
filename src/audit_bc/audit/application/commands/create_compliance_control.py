from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.domain.entities import ComplianceControl
from src.audit_bc.audit.domain.exceptions import ControlCodeExistsError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class CreateComplianceControlCommand(Command):
    company_id: str
    code: str
    name: str
    framework: str
    description: Optional[str] = None


class CreateComplianceControlHandler(
    CommandHandler[CreateComplianceControlCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: CreateComplianceControlCommand) -> None:
        existing = self.repo.find_control_by_code(
            command.code, company_id=command.company_id
        )
        if existing:
            raise ControlCodeExistsError(
                f"Control code '{command.code}' already exists"
            )

        control = ComplianceControl.create(
            company_id=command.company_id,
            code=command.code,
            name=command.name,
            framework=command.framework,
            description=command.description,
        )
        self.repo.save_control(control)
