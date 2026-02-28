from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.update_bia import (
    AssetNotFoundError,
    UpdateBiaCommand,
    UpdateBiaCommandHandler,
)
from src.asset_bc.asset.domain.entities import Asset, AssetDecommissionedError
from src.asset_bc.asset.domain.enums import AssetStatus


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1",
        type="laptop",
        brand="Dell",
        model="Latitude",
        serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


class TestUpdateBiaCommand:
    def test_happy_path(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UpdateBiaCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateBiaCommand(
                asset_id=asset.id,
                company_id="comp1",
                performed_by="user1",
                impact_score=5,
                rto_minutes=60,
                rpo_minutes=30,
                bia_justification="Critical server",
            )
        )

        assert asset.impact_score == 5
        assert asset.rto_minutes == 60
        assert asset.rpo_minutes == 30
        assert asset.bia_justification == "Critical server"
        assert asset.bia_reviewed_by == "user1"
        assert asset.bia_reviewed_at is not None
        repo.save.assert_called_once()
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "bia_updated"
        assert "impact_score" in event.data
        assert "rto_minutes" in event.data
        assert "rpo_minutes" in event.data
        assert "bia_justification" in event.data

    def test_no_changes_no_event(self):
        asset = _make_asset()
        asset.impact_score = 5
        asset.rto_minutes = 60
        asset.rpo_minutes = 30
        asset.bia_justification = "Same"
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = UpdateBiaCommandHandler(asset_repo=repo)

        handler.handle(
            UpdateBiaCommand(
                asset_id=asset.id,
                company_id="comp1",
                performed_by="user1",
                impact_score=5,
                rto_minutes=60,
                rpo_minutes=30,
                bia_justification="Same",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_not_called()

    def test_asset_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateBiaCommandHandler(asset_repo=repo)

        with pytest.raises(AssetNotFoundError):
            handler.handle(
                UpdateBiaCommand(
                    asset_id="bad",
                    company_id="comp1",
                    performed_by="user1",
                    impact_score=5,
                )
            )
        repo.save.assert_not_called()

    def test_invalid_impact_score_raises(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = UpdateBiaCommandHandler(asset_repo=repo)

        with pytest.raises(ValueError, match="impact_score must be between 1 and 10"):
            handler.handle(
                UpdateBiaCommand(
                    asset_id=asset.id,
                    company_id="comp1",
                    performed_by="user1",
                    impact_score=0,
                )
            )
        repo.save.assert_not_called()

    def test_decommissioned_raises(self):
        asset = _make_asset()
        asset.status = AssetStatus.DECOMMISSIONED
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = UpdateBiaCommandHandler(asset_repo=repo)

        with pytest.raises(AssetDecommissionedError):
            handler.handle(
                UpdateBiaCommand(
                    asset_id=asset.id,
                    company_id="comp1",
                    performed_by="user1",
                    impact_score=5,
                    rto_minutes=60,
                    rpo_minutes=30,
                    bia_justification="test",
                )
            )
        repo.save.assert_not_called()
