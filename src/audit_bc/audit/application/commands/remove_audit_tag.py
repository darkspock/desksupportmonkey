from dataclasses import dataclass

from src.audit_bc.audit.domain.exceptions import AuditEntryNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class RemoveAuditTagCommand(Command):
    tag_id: str
    entry_id: str
    company_id: str


class RemoveAuditTagHandler(CommandHandler[RemoveAuditTagCommand]):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: RemoveAuditTagCommand) -> None:
        entry = self.repo.find_by_id(
            command.entry_id, company_id=command.company_id
        )
        if entry is None:
            raise AuditEntryNotFoundError(
                f"Audit entry {command.entry_id} not found"
            )

        self.repo.delete_tag(command.tag_id)
