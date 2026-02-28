from dataclasses import dataclass
from typing import Optional

from src.asset_bc.asset.domain.entities import AssetEvent, CIRelationship
from src.asset_bc.asset.domain.enums import AssetStatus, CIRelationshipType
from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
    CIRelationshipRepositoryInterface,
)
from src.framework.application.command_bus import Command, CommandHandler


class AssetNotFoundError(Exception):
    pass


class SelfReferenceError(Exception):
    pass


class DuplicateRelationshipError(Exception):
    pass


class DecommissionedTargetError(Exception):
    pass


@dataclass
class CreateCIRelationshipCommand(Command):
    company_id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    performed_by: str
    description: Optional[str] = None


class CreateCIRelationshipCommandHandler(CommandHandler[CreateCIRelationshipCommand]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        ci_repo: CIRelationshipRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.ci_repo = ci_repo

    def handle(self, command: CreateCIRelationshipCommand) -> None:
        if command.source_asset_id == command.target_asset_id:
            raise SelfReferenceError("Cannot create relationship to self")

        source = self.asset_repo.find_by_id(command.source_asset_id, command.company_id)
        if not source:
            raise AssetNotFoundError(f"Source asset '{command.source_asset_id}' not found")

        target = self.asset_repo.find_by_id(command.target_asset_id, command.company_id)
        if not target:
            raise AssetNotFoundError(f"Target asset '{command.target_asset_id}' not found")

        if target.status == AssetStatus.DECOMMISSIONED:
            raise DecommissionedTargetError("Cannot create relationship to decommissioned asset")

        rel_type = CIRelationshipType(command.relationship_type)

        duplicate = self.ci_repo.find_duplicate(
            command.source_asset_id, command.target_asset_id, rel_type.value, command.company_id,
        )
        if duplicate:
            raise DuplicateRelationshipError("Relationship already exists")

        relationship = CIRelationship.create(
            company_id=command.company_id,
            source_asset_id=command.source_asset_id,
            target_asset_id=command.target_asset_id,
            relationship_type=rel_type,
            created_by=command.performed_by,
            description=command.description,
        )

        self.ci_repo.save(relationship)

        event = AssetEvent.create(
            asset_id=source.id,
            event_type="ci_relationship_created",
            data={
                "relationship_id": relationship.id,
                "target_asset_id": command.target_asset_id,
                "relationship_type": rel_type.value,
            },
            performed_by=command.performed_by,
        )
        self.asset_repo.save_event(event)
