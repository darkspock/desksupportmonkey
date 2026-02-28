from dataclasses import dataclass

from src.asset_bc.asset.domain.entities import AssetEvent
from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
    CIRelationshipRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler


class CIRelationshipNotFoundError(Exception):
    pass


@dataclass
class DeleteCIRelationshipCommand(Command):
    relationship_id: str
    company_id: str
    source_asset_id: str
    performed_by: str


class DeleteCIRelationshipCommandHandler(CommandHandler[DeleteCIRelationshipCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        ci_repo: CIRelationshipRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.ci_repo = ci_repo

    def handle(self, command: DeleteCIRelationshipCommand) -> None:
        relationship = self.ci_repo.find_by_id(command.relationship_id, command.company_id)
        if not relationship:
            raise CIRelationshipNotFoundError(f"Relationship '{command.relationship_id}' not found")

        target_asset_id = relationship.target_asset_id
        relationship_type = relationship.relationship_type.value

        self.ci_repo.delete(relationship.id)

        event = AssetEvent.create(
            asset_id=command.source_asset_id,
            event_type="ci_relationship_deleted",
            data={
                "relationship_id": relationship.id,
                "target_asset_id": target_asset_id,
                "relationship_type": relationship_type,
            },
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)
