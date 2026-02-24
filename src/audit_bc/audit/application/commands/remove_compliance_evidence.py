from dataclasses import dataclass

from src.audit_bc.audit.domain.exceptions import EvidenceNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class RemoveComplianceEvidenceCommand(Command):
    evidence_id: str
    company_id: str


class RemoveComplianceEvidenceHandler(
    CommandHandler[RemoveComplianceEvidenceCommand]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: RemoveComplianceEvidenceCommand) -> None:
        evidence = self.repo.find_evidence_by_id(
            command.evidence_id, command.company_id
        )
        if not evidence:
            raise EvidenceNotFoundError(
                f"Evidence '{command.evidence_id}' not found"
            )
        self.repo.delete_evidence(command.evidence_id)
