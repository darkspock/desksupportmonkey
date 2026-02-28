from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.commands.set_criticality import (
    AssetNotFoundError,
    SetCriticalityCommand,
    SetCriticalityCommandHandler,
)
from src.asset_bc.asset.domain.entities import Asset, AssetDecommissionedError
from src.asset_bc.asset.domain.enums import AssetCriticality, AssetStatus


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


class TestSetCriticalityCommand:
    def test_set_criticality_to_critical(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = SetCriticalityCommandHandler(asset_repo=repo)

        handler.handle(
            SetCriticalityCommand(
                asset_id=asset.id,
                company_id="comp1",
                criticality="critical",
                performed_by="user1",
            )
        )

        assert asset.criticality == AssetCriticality.CRITICAL
        repo.save.assert_called_once()
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "criticality_set"
        assert event.data == {"old": None, "new": "critical"}

    def test_clear_criticality_none(self):
        asset = _make_asset()
        asset.criticality = AssetCriticality.HIGH
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = SetCriticalityCommandHandler(asset_repo=repo)

        handler.handle(
            SetCriticalityCommand(
                asset_id=asset.id,
                company_id="comp1",
                criticality=None,
                performed_by="user1",
            )
        )

        assert asset.criticality is None
        repo.save.assert_called_once()
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == "criticality_set"
        assert event.data == {"old": "high", "new": None}

    def test_same_value_no_event(self):
        asset = _make_asset()
        asset.criticality = AssetCriticality.MEDIUM
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.save.side_effect = lambda a: a
        handler = SetCriticalityCommandHandler(asset_repo=repo)

        handler.handle(
            SetCriticalityCommand(
                asset_id=asset.id,
                company_id="comp1",
                criticality="medium",
                performed_by="user1",
            )
        )

        repo.save.assert_called_once()
        repo.save_event.assert_not_called()

    def test_asset_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = SetCriticalityCommandHandler(asset_repo=repo)

        with pytest.raises(AssetNotFoundError):
            handler.handle(
                SetCriticalityCommand(
                    asset_id="bad",
                    company_id="comp1",
                    criticality="critical",
                    performed_by="user1",
                )
            )
        repo.save.assert_not_called()

    def test_decommissioned_asset_raises(self):
        asset = _make_asset()
        asset.status = AssetStatus.DECOMMISSIONED
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = SetCriticalityCommandHandler(asset_repo=repo)

        with pytest.raises(AssetDecommissionedError):
            handler.handle(
                SetCriticalityCommand(
                    asset_id=asset.id,
                    company_id="comp1",
                    criticality="critical",
                    performed_by="user1",
                )
            )
        repo.save.assert_not_called()
