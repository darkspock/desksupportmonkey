from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.link_assets import (
    LinkAssetsCommand,
    LinkAssetsCommandHandler,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    InvalidStatusTransitionError,
)
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
ACTOR_ID = "01USER00000000000000000001"
ASSET_ID_1 = "01ASSET000000000000000001"
ASSET_ID_2 = "01ASSET000000000000000002"


def _make_command(**overrides) -> LinkAssetsCommand:
    defaults = dict(
        change_id=CHANGE_ID,
        company_id=COMPANY_ID,
        asset_ids=[ASSET_ID_1, ASSET_ID_2],
        actor_id=ACTOR_ID,
    )
    defaults.update(overrides)
    return LinkAssetsCommand(**defaults)


def _make_mock_change(status: ChangeStatus = ChangeStatus.DRAFT) -> MagicMock:
    change = MagicMock()
    change.status = status
    return change


class TestLinkAssetsCommand:
    def test_link_assets_success(self):
        mock_change = _make_mock_change(ChangeStatus.DRAFT)
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = mock_change
        change_repo.find_assets_by_change.return_value = []

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = MagicMock()  # truthy asset

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )
        handler.handle(_make_command(asset_ids=[ASSET_ID_1]))

        change_repo.save_change_asset.assert_called_once()
        change_repo.save_event.assert_called_once()
        event = change_repo.save_event.call_args[0][0]
        assert event.event_type == ChangeEventType.ASSET_LINKED

    def test_link_assets_skips_duplicates(self):
        existing_link = MagicMock()
        existing_link.asset_id = ASSET_ID_1

        mock_change = _make_mock_change(ChangeStatus.DRAFT)
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = mock_change
        change_repo.find_assets_by_change.return_value = [existing_link]

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = MagicMock()

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )
        handler.handle(_make_command(asset_ids=[ASSET_ID_1, ASSET_ID_2]))

        # Only ASSET_ID_2 should be linked (ASSET_ID_1 already exists)
        change_repo.save_change_asset.assert_called_once()
        ca = change_repo.save_change_asset.call_args[0][0]
        assert ca.asset_id == ASSET_ID_2

    def test_link_assets_skips_invalid_assets(self):
        mock_change = _make_mock_change(ChangeStatus.DRAFT)
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = mock_change
        change_repo.find_assets_by_change.return_value = []

        asset_repo = MagicMock()
        asset_repo.find_by_id.return_value = None  # asset not found

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )
        handler.handle(_make_command(asset_ids=[ASSET_ID_1]))

        change_repo.save_change_asset.assert_not_called()

    def test_link_assets_terminal_state_raises(self):
        mock_change = _make_mock_change(ChangeStatus.CLOSED)
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = mock_change

        asset_repo = MagicMock()

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(_make_command())

        change_repo.save_change_asset.assert_not_called()
        change_repo.save_event.assert_not_called()

    def test_link_assets_change_not_found_raises(self):
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = None

        asset_repo = MagicMock()

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )

        with pytest.raises(ChangeNotFoundError):
            handler.handle(_make_command())

        change_repo.save_change_asset.assert_not_called()
        change_repo.save_event.assert_not_called()

    def test_link_assets_no_event_when_none_linked(self):
        existing_link = MagicMock()
        existing_link.asset_id = ASSET_ID_1

        mock_change = _make_mock_change(ChangeStatus.DRAFT)
        change_repo = MagicMock()
        change_repo.find_by_id.return_value = mock_change
        change_repo.find_assets_by_change.return_value = [existing_link]

        asset_repo = MagicMock()

        handler = LinkAssetsCommandHandler(
            change_repo=change_repo, asset_repo=asset_repo
        )
        # Only pass the already-existing asset id so all are skipped
        handler.handle(_make_command(asset_ids=[ASSET_ID_1]))

        change_repo.save_change_asset.assert_not_called()
        change_repo.save_event.assert_not_called()
