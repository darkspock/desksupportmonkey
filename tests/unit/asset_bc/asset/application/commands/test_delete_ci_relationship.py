from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.delete_ci_relationship import (
    CIRelationshipNotFoundError,
    DeleteCIRelationshipCommand,
    DeleteCIRelationshipCommandHandler,
)
from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.enums import CIRelationshipType


def _make_relationship():
    return CIRelationship.create(
        company_id="comp1",
        source_asset_id="src1",
        target_asset_id="tgt1",
        relationship_type=CIRelationshipType.DEPENDS_ON,
        created_by="user1",
        description="Some dependency",
    )


class TestDeleteCIRelationshipCommand:
    def test_delete_success(self):
        relationship = _make_relationship()
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = relationship
        asset_repo = MagicMock()

        handler = DeleteCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        handler.handle(
            DeleteCIRelationshipCommand(
                relationship_id=relationship.id,
                company_id="comp1",
                source_asset_id="src1",
                performed_by="user1",
            )
        )

        ci_repo.delete.assert_called_once_with(relationship.id)
        asset_repo.save_event.assert_called_once()

    def test_not_found_raises(self):
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = None
        asset_repo = MagicMock()

        handler = DeleteCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        with pytest.raises(CIRelationshipNotFoundError):
            handler.handle(
                DeleteCIRelationshipCommand(
                    relationship_id="missing",
                    company_id="comp1",
                    source_asset_id="src1",
                    performed_by="user1",
                )
            )

        ci_repo.delete.assert_not_called()
        asset_repo.save_event.assert_not_called()

    def test_event_recorded_on_source(self):
        relationship = _make_relationship()
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = relationship
        asset_repo = MagicMock()

        handler = DeleteCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        handler.handle(
            DeleteCIRelationshipCommand(
                relationship_id=relationship.id,
                company_id="comp1",
                source_asset_id="src1",
                performed_by="user1",
            )
        )

        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "ci_relationship_deleted"
        assert event.asset_id == "src1"
        assert event.data["relationship_id"] == relationship.id
        assert event.data["target_asset_id"] == "tgt1"
        assert event.data["relationship_type"] == "depends_on"
