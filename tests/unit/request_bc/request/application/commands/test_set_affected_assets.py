from unittest.mock import MagicMock, call

import pytest

from src.request_bc.request.application.commands.set_affected_assets import (
    AssetNotFoundError,
    RequestNotFoundError,
    SetAffectedAssetsCommand,
    SetAffectedAssetsCommandHandler,
)


def _make_mock_request(
    request_id: str = "r1",
    company_id: str = "c1",
    data: dict | None = None,
):
    req = MagicMock()
    req.id = request_id
    req.company_id = company_id
    req.data = data if data is not None else {}
    return req


def _make_mock_asset(asset_id: str):
    asset = MagicMock()
    asset.id = asset_id
    return asset


class TestSetAffectedAssetsCommand:
    def setup_method(self):
        self.request_repo = MagicMock()
        self.asset_repo = MagicMock()
        self.handler = SetAffectedAssetsCommandHandler(
            request_repo=self.request_repo,
            asset_repo=self.asset_repo,
        )

    def test_happy_path_sets_affected_assets(self):
        request = _make_mock_request(data={})
        self.request_repo.find_by_id.return_value = request

        asset1 = _make_mock_asset("a1")
        asset2 = _make_mock_asset("a2")
        self.asset_repo.find_by_ids.return_value = [asset1, asset2]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1", "a2"],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        assert request.data["affected_asset_ids"] == ["a1", "a2"]
        self.request_repo.save.assert_called_once_with(request)
        self.request_repo.save_event.assert_called_once()

    def test_request_not_found_raises(self):
        self.request_repo.find_by_id.return_value = None

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1"],
            performed_by="user1",
        )
        with pytest.raises(RequestNotFoundError, match="r1"):
            self.handler.handle(cmd)

        self.request_repo.save.assert_not_called()

    def test_asset_not_found_raises(self):
        request = _make_mock_request()
        self.request_repo.find_by_id.return_value = request

        # Only a1 found, a2 is missing
        self.asset_repo.find_by_ids.return_value = [_make_mock_asset("a1")]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1", "a2"],
            performed_by="user1",
        )
        with pytest.raises(AssetNotFoundError, match="a2"):
            self.handler.handle(cmd)

        self.request_repo.save.assert_not_called()

    def test_merges_into_existing_data(self):
        """Affected assets are merged into existing data, not overwriting other keys."""
        existing_data = {"ai_classification": {"ai_used": True, "category": "hardware"}}
        request = _make_mock_request(data=existing_data)
        self.request_repo.find_by_id.return_value = request

        self.asset_repo.find_by_ids.return_value = [_make_mock_asset("a1")]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1"],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        # Original keys preserved
        assert request.data["ai_classification"] == {
            "ai_used": True,
            "category": "hardware",
        }
        # New key added
        assert request.data["affected_asset_ids"] == ["a1"]

    def test_empty_asset_ids_clears_affected(self):
        """Empty asset_ids list is allowed and clears existing affected assets."""
        request = _make_mock_request(
            data={"affected_asset_ids": ["a1", "a2"]},
        )
        self.request_repo.find_by_id.return_value = request

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=[],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        assert request.data["affected_asset_ids"] == []
        self.request_repo.save.assert_called_once_with(request)
        # asset_repo.find_by_ids not called for empty list
        self.asset_repo.find_by_ids.assert_not_called()

    def test_records_event_with_old_and_new_ids(self):
        request = _make_mock_request(
            data={"affected_asset_ids": ["old1"]},
        )
        self.request_repo.find_by_id.return_value = request

        self.asset_repo.find_by_ids.return_value = [_make_mock_asset("new1")]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["new1"],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        self.request_repo.save_event.assert_called_once()
        event = self.request_repo.save_event.call_args[0][0]
        assert event.request_id == "r1"
        assert event.event_type == "affected_assets_updated"
        assert event.data["old_asset_ids"] == ["old1"]
        assert event.data["new_asset_ids"] == ["new1"]
        assert event.performed_by == "user1"

    def test_records_event_with_empty_old_ids_when_no_previous(self):
        request = _make_mock_request(data={})
        self.request_repo.find_by_id.return_value = request

        self.asset_repo.find_by_ids.return_value = [_make_mock_asset("a1")]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1"],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        event = self.request_repo.save_event.call_args[0][0]
        assert event.data["old_asset_ids"] == []
        assert event.data["new_asset_ids"] == ["a1"]

    def test_initializes_data_dict_when_none(self):
        """When request.data is None, it gets initialized to a dict."""
        request = _make_mock_request(data=None)
        request.data = None
        self.request_repo.find_by_id.return_value = request

        self.asset_repo.find_by_ids.return_value = [_make_mock_asset("a1")]

        cmd = SetAffectedAssetsCommand(
            request_id="r1",
            company_id="c1",
            asset_ids=["a1"],
            performed_by="user1",
        )
        self.handler.handle(cmd)

        assert request.data == {"affected_asset_ids": ["a1"]}
        self.request_repo.save.assert_called_once()
