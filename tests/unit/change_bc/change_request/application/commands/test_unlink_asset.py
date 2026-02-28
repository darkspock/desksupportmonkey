from unittest.mock import MagicMock

import pytest

from src.change_bc.change_request.application.commands.unlink_asset import (
    UnlinkAssetCommand,
    UnlinkAssetCommandHandler,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    ChangeNotUnlinkableError,
)


CHANGE_ID = "01CHANGE000000000000000001"
COMPANY_ID = "01COMPANY00000000000000001"
ACTOR_ID = "01USER00000000000000000001"
ASSET_ID = "01ASSET000000000000000001"


def _make_command(**overrides) -> UnlinkAssetCommand:
    defaults = dict(
        change_id=CHANGE_ID,
        company_id=COMPANY_ID,
        asset_id=ASSET_ID,
        actor_id=ACTOR_ID,
    )
    defaults.update(overrides)
    return UnlinkAssetCommand(**defaults)


def _make_mock_change(status: ChangeStatus = ChangeStatus.DRAFT) -> MagicMock:
    change = MagicMock()
    change.status = status
    return change


class TestUnlinkAssetCommand:
    def test_unlink_asset_success_draft(self):
        mock_change = _make_mock_change(ChangeStatus.DRAFT)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)
        handler.handle(_make_command())

        repo.delete_change_asset.assert_called_once_with(CHANGE_ID, ASSET_ID)
        repo.save_event.assert_called_once()
        event = repo.save_event.call_args[0][0]
        assert event.event_type == ChangeEventType.ASSET_UNLINKED
        assert event.metadata == {"asset_id": ASSET_ID}

    def test_unlink_asset_success_pending_approval(self):
        mock_change = _make_mock_change(ChangeStatus.PENDING_APPROVAL)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)
        handler.handle(_make_command())

        repo.delete_change_asset.assert_called_once_with(CHANGE_ID, ASSET_ID)
        repo.save_event.assert_called_once()

    def test_unlink_asset_success_scheduled(self):
        mock_change = _make_mock_change(ChangeStatus.SCHEDULED)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)
        handler.handle(_make_command())

        repo.delete_change_asset.assert_called_once_with(CHANGE_ID, ASSET_ID)
        repo.save_event.assert_called_once()

    def test_unlink_asset_in_progress_raises(self):
        mock_change = _make_mock_change(ChangeStatus.IN_PROGRESS)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotUnlinkableError):
            handler.handle(_make_command())

        repo.delete_change_asset.assert_not_called()
        repo.save_event.assert_not_called()

    def test_unlink_asset_implemented_raises(self):
        mock_change = _make_mock_change(ChangeStatus.IMPLEMENTED)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotUnlinkableError):
            handler.handle(_make_command())

        repo.delete_change_asset.assert_not_called()
        repo.save_event.assert_not_called()

    def test_unlink_asset_terminal_raises(self):
        mock_change = _make_mock_change(ChangeStatus.CLOSED)
        repo = MagicMock()
        repo.find_by_id.return_value = mock_change

        handler = UnlinkAssetCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotUnlinkableError):
            handler.handle(_make_command())

        repo.delete_change_asset.assert_not_called()
        repo.save_event.assert_not_called()

    def test_unlink_asset_change_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UnlinkAssetCommandHandler(change_repo=repo)

        with pytest.raises(ChangeNotFoundError):
            handler.handle(_make_command())

        repo.delete_change_asset.assert_not_called()
        repo.save_event.assert_not_called()
