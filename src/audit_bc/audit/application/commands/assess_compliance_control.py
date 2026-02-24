from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.domain.entities import ComplianceAssessment
from src.audit_bc.audit.domain.enums import ComplianceStatus
from src.audit_bc.audit.domain.exceptions import (
    ControlNotFoundError,
    InvalidComplianceStatusError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class AssessComplianceControlCommand(Command):
    company_id: str
    control_id: str
    status: str
    assessed_by: str
    notes: Optional[str] = None


class AssessComplianceControlHandler(
    CommandHandler[AssessComplianceControlCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: AssessComplianceControlCommand) -> None:
        control = self.repo.find_control_by_id(
            command.control_id, company_id=command.company_id
        )
        if not control:
            raise ControlNotFoundError(
                f"Control '{command.control_id}' not found"
            )

        try:
            status = ComplianceStatus(command.status)
        except ValueError:
            raise InvalidComplianceStatusError(
                f"Invalid compliance status: '{command.status}'"
            )

        existing = self.repo.find_assessment(
            command.company_id, command.control_id
        )
        if existing:
            existing.update_status(
                status=status,
                notes=command.notes,
                assessed_by=command.assessed_by,
            )
            self.repo.save_assessment(existing)
        else:
            assessment = ComplianceAssessment.create(
                company_id=command.company_id,
                control_id=command.control_id,
                status=status,
                assessed_by=command.assessed_by,
                notes=command.notes,
            )
            self.repo.save_assessment(assessment)
