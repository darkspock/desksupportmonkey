from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.create_ci_relationship import (
    AssetNotFoundError,
    CreateCIRelationshipCommand,
    CreateCIRelationshipCommandHandler,
    DecommissionedTargetError,
    DuplicateRelationshipError,
    SelfReferenceError,
)
from src.asset_bc.asset.domain.enums import AssetStatus


def _make_asset(asset_id="a1", status=AssetStatus.IN_STOCK):
    asset = MagicMock()
    asset.id = asset_id
    asset.status = status
    return asset


def _make_handler(asset_repo=None, ci_repo=None):
    asset_repo = asset_repo or MagicMock()
    ci_repo = ci_repo or MagicMock()
    return CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo), asset_repo, ci_repo


class TestCreateCIRelationshipCommand:
    def test_create_success(self):
        source = _make_asset(asset_id="src1")
        target = _make_asset(asset_id="tgt1")
        asset_repo = MagicMock()
        asset_repo.find_by_id.side_effect = lambda aid, cid: (
            source if aid == "src1" else target if aid == "tgt1" else None
        )
        ci_repo = MagicMock()
        ci_repo.find_duplicate.return_value = None

        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        handler.handle(
            CreateCIRelationshipCommand(
                company_id="comp1",
                source_asset_id="src1",
                target_asset_id="tgt1",
                relationship_type="depends_on",
                performed_by="user1",
                description="App depends on DB",
            )
        )

        ci_repo.save.assert_called_once()
        asset_repo.save_event.assert_called_once()

    def test_self_reference_raises(self):
        handler, asset_repo, ci_repo = _make_handler()

        with pytest.raises(SelfReferenceError):
            handler.handle(
                CreateCIRelationshipCommand(
                    company_id="comp1",
                    source_asset_id="same_id",
                    target_asset_id="same_id",
                    relationship_type="depends_on",
                    performed_by="user1",
                )
            )

        ci_repo.save.assert_not_called()

    def test_source_not_found_raises(self):
        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None
        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=MagicMock())

        with pytest.raises(AssetNotFoundError, match="Source asset"):
            handler.handle(
                CreateCIRelationshipCommand(
                    company_id="comp1",
                    source_asset_id="missing",
                    target_asset_id="tgt1",
                    relationship_type="depends_on",
                    performed_by="user1",
                )
            )

    def test_target_not_found_raises(self):
        source = _make_asset(asset_id="src1")
        asset_repo = MagicMock()
        asset_repo.find_by_id.side_effect = lambda aid, cid: (
            source if aid == "src1" else None
        )
        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=MagicMock())

        with pytest.raises(AssetNotFoundError, match="Target asset"):
            handler.handle(
                CreateCIRelationshipCommand(
                    company_id="comp1",
                    source_asset_id="src1",
                    target_asset_id="missing",
                    relationship_type="depends_on",
                    performed_by="user1",
                )
            )

    def test_decommissioned_target_raises(self):
        source = _make_asset(asset_id="src1")
        target = _make_asset(asset_id="tgt1", status=AssetStatus.DECOMMISSIONED)
        asset_repo = MagicMock()
        asset_repo.find_by_id.side_effect = lambda aid, cid: (
            source if aid == "src1" else target if aid == "tgt1" else None
        )
        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=MagicMock())

        with pytest.raises(DecommissionedTargetError):
            handler.handle(
                CreateCIRelationshipCommand(
                    company_id="comp1",
                    source_asset_id="src1",
                    target_asset_id="tgt1",
                    relationship_type="depends_on",
                    performed_by="user1",
                )
            )

    def test_duplicate_raises(self):
        source = _make_asset(asset_id="src1")
        target = _make_asset(asset_id="tgt1")
        asset_repo = MagicMock()
        asset_repo.find_by_id.side_effect = lambda aid, cid: (
            source if aid == "src1" else target if aid == "tgt1" else None
        )
        ci_repo = MagicMock()
        ci_repo.find_duplicate.return_value = MagicMock()  # existing relationship

        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        with pytest.raises(DuplicateRelationshipError):
            handler.handle(
                CreateCIRelationshipCommand(
                    company_id="comp1",
                    source_asset_id="src1",
                    target_asset_id="tgt1",
                    relationship_type="depends_on",
                    performed_by="user1",
                )
            )

        ci_repo.save.assert_not_called()

    def test_event_recorded_on_source(self):
        source = _make_asset(asset_id="src1")
        target = _make_asset(asset_id="tgt1")
        asset_repo = MagicMock()
        asset_repo.find_by_id.side_effect = lambda aid, cid: (
            source if aid == "src1" else target if aid == "tgt1" else None
        )
        ci_repo = MagicMock()
        ci_repo.find_duplicate.return_value = None

        handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)

        handler.handle(
            CreateCIRelationshipCommand(
                company_id="comp1",
                source_asset_id="src1",
                target_asset_id="tgt1",
                relationship_type="depends_on",
                performed_by="user1",
            )
        )

        asset_repo.save_event.assert_called_once()
        event = asset_repo.save_event.call_args[0][0]
        assert event.event_type == "ci_relationship_created"
        assert event.asset_id == "src1"
        assert event.data["target_asset_id"] == "tgt1"
        assert event.data["relationship_type"] == "depends_on"
        assert "relationship_id" in event.data
