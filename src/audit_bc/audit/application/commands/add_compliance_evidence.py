from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.domain.entities import ComplianceEvidence
from src.audit_bc.audit.domain.enums import EvidenceType
from src.audit_bc.audit.domain.exceptions import ControlNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class AddComplianceEvidenceCommand(Command):
    company_id: str
    control_id: str
    evidence_type: str
    title: str
    added_by: str
    reference_id: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None


class AddComplianceEvidenceHandler(
    CommandHandler[AddComplianceEvidenceCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: AddComplianceEvidenceCommand) -> None:
        control = self.repo.find_control_by_id(
            command.control_id, company_id=command.company_id
        )
        if not control:
            raise ControlNotFoundError(
                f"Control '{command.control_id}' not found"
            )

        evidence_type = EvidenceType(command.evidence_type)

        evidence = ComplianceEvidence.create(
            company_id=command.company_id,
            control_id=command.control_id,
            evidence_type=evidence_type,
            title=command.title,
            added_by=command.added_by,
            reference_id=command.reference_id,
            description=command.description,
            url=command.url,
        )
        self.repo.save_evidence(evidence)
