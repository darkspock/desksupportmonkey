from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.update_ci_relationship import (
    CIRelationshipNotFoundError,
    UpdateCIRelationshipCommand,
    UpdateCIRelationshipCommandHandler,
)
from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.enums import CIRelationshipType


def _make_relationship(description="Original description"):
    return CIRelationship.create(
        company_id="comp1",
        source_asset_id="a1",
        target_asset_id="a2",
        relationship_type=CIRelationshipType.DEPENDS_ON,
        created_by="user1",
        description=description,
    )


class TestUpdateCIRelationshipCommand:
    def test_update_success(self):
        relationship = _make_relationship(description="Old desc")
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = relationship

        handler = UpdateCIRelationshipCommandHandler(ci_repo=ci_repo)

        handler.handle(
            UpdateCIRelationshipCommand(
                relationship_id=relationship.id,
                company_id="comp1",
                description="New desc",
                performed_by="user1",
            )
        )

        assert relationship.description == "New desc"
        ci_repo.save.assert_called_once_with(relationship)

    def test_not_found_raises(self):
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = None

        handler = UpdateCIRelationshipCommandHandler(ci_repo=ci_repo)

        with pytest.raises(CIRelationshipNotFoundError):
            handler.handle(
                UpdateCIRelationshipCommand(
                    relationship_id="missing",
                    company_id="comp1",
                    description="New desc",
                    performed_by="user1",
                )
            )

        ci_repo.save.assert_not_called()

    def test_no_change_does_not_save(self):
        relationship = _make_relationship(description="Same value")
        ci_repo = MagicMock()
        ci_repo.find_by_id.return_value = relationship

        handler = UpdateCIRelationshipCommandHandler(ci_repo=ci_repo)

        handler.handle(
            UpdateCIRelationshipCommand(
                relationship_id=relationship.id,
                company_id="comp1",
                description="Same value",
                performed_by="user1",
            )
        )

        assert relationship.description == "Same value"
        ci_repo.save.assert_not_called()
