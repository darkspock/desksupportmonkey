from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.repository import CIRelationshipRepositoryInterface
from src.framework.application.command_bus import Command, CommandHandler


class CIRelationshipNotFoundError(Exception):
    pass


@dataclass
class UpdateCIRelationshipCommand(Command):
    relationship_id: str
    company_id: str
    description: Optional[str]
    performed_by: str


class UpdateCIRelationshipCommandHandler(CommandHandler[UpdateCIRelationshipCommand]):
    def __init__(self, ci_repo: CIRelationshipRepositoryInterface):
        self.ci_repo = ci_repo

    def handle(self, command: UpdateCIRelationshipCommand) -> None:
        relationship = self.ci_repo.find_by_id(command.relationship_id, command.company_id)
        if not relationship:
            raise CIRelationshipNotFoundError(f"Relationship '{command.relationship_id}' not found")

        changes = relationship.update_description(command.description)
        if changes:
            self.ci_repo.save(relationship)
