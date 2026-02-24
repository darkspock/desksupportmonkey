from dataclasses import dataclass

from src.audit_bc.audit.domain.entities import AuditEntryTag
from src.audit_bc.audit.domain.exceptions import (
    AuditEntryNotFoundError,
    ControlNotFoundError,
)
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


@dataclass
class AddAuditTagsCommand(Command):
    entry_id: str
    company_id: str
    control_ids: list[str]
    tagged_by: str


class AddAuditTagsHandler(CommandHandler[AddAuditTagsCommand]):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, command: AddAuditTagsCommand) -> None:
        entry = self.repo.find_by_id(
            command.entry_id, company_id=command.company_id
        )
        if entry is None:
            raise AuditEntryNotFoundError(
                f"Audit entry {command.entry_id} not found"
            )

        # Get existing tags to skip duplicates
        existing_tags = self.repo.find_tags_by_entry(command.entry_id)
        existing_control_ids = {t.control_id for t in existing_tags}

        for control_id in command.control_ids:
            if control_id in existing_control_ids:
                continue

            control = self.repo.find_control_by_id(
                control_id, company_id=command.company_id
            )
            if control is None:
                raise ControlNotFoundError(
                    f"Control {control_id} not found"
                )

            tag = AuditEntryTag.create(
                audit_entry_id=command.entry_id,
                control_id=control_id,
                tagged_by=command.tagged_by,
            )
            self.repo.save_tag(tag)
