from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.queries.list_assets import (
    ListAssetsQuery,
    ListAssetsQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset import (
    AssetNotFoundError as GetNotFoundError,
    GetAssetQuery,
    GetAssetQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset_history import (
    AssetNotFoundError as HistoryNotFoundError,
    GetAssetHistoryQuery,
    GetAssetHistoryQueryHandler,
)
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset, AssetEvent
from src.asset_bc.asset.domain.enums import AssetStatus, AssetType


def _make_asset(**overrides):
    defaults = dict(
        company_id="comp1",
        type=AssetType.LAPTOP,
        brand="Dell",
        model="Latitude",
        serial_number="SN001",
    )
    defaults.update(overrides)
    return Asset.create(**defaults)


class TestListAssetsQuery:
    def test_returns_paginated(self):
        assets = [_make_asset(serial_number=f"SN{i}") for i in range(3)]
        repo = MagicMock()
        repo.find_all.return_value = (assets, 3)
        handler = ListAssetsQueryHandler(asset_repo=repo)

        result, total = handler.handle(
            ListAssetsQuery(company_id="comp1", page=1, page_size=20)
        )

        assert len(result) == 3
        assert total == 3
        repo.find_all.assert_called_once_with(
            company_id="comp1", page=1, page_size=20,
            search=None, type=None, status=None,
            department_id=None, assigned_to=None,
            sort_by="created_at", sort_order="desc",
        )

    def test_with_search_param(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAssetsQueryHandler(asset_repo=repo)

        handler.handle(ListAssetsQuery(company_id="comp1", search="dell"))

        repo.find_all.assert_called_once()
        call_kwargs = repo.find_all.call_args.kwargs
        assert call_kwargs["search"] == "dell"

    def test_with_type_filter(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAssetsQueryHandler(asset_repo=repo)

        handler.handle(ListAssetsQuery(company_id="comp1", type="laptop"))

        call_kwargs = repo.find_all.call_args.kwargs
        assert call_kwargs["type"] == "laptop"

    def test_with_sort(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListAssetsQueryHandler(asset_repo=repo)

        handler.handle(
            ListAssetsQuery(company_id="comp1", sort_by="purchase_date", sort_order="asc")
        )

        call_kwargs = repo.find_all.call_args.kwargs
        assert call_kwargs["sort_by"] == "purchase_date"
        assert call_kwargs["sort_order"] == "asc"


class TestGetAssetQuery:
    def test_success(self):
        asset = _make_asset()
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        handler = GetAssetQueryHandler(asset_repo=repo)

        result = handler.handle(GetAssetQuery(asset_id=asset.id, company_id="comp1"))

        assert result.id == asset.id

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetAssetQueryHandler(asset_repo=repo)

        with pytest.raises(GetNotFoundError):
            handler.handle(GetAssetQuery(asset_id="bad", company_id="comp1"))


class TestGetAssetHistoryQuery:
    def test_success(self):
        asset = _make_asset()
        events = [
            AssetEvent.create(asset_id=asset.id, event_type="created", data={}, performed_by="u1"),
        ]
        repo = MagicMock()
        repo.find_by_id.return_value = asset
        repo.find_events.return_value = events
        handler = GetAssetHistoryQueryHandler(asset_repo=repo)

        result = handler.handle(
            GetAssetHistoryQuery(asset_id=asset.id, company_id="comp1")
        )

        assert len(result) == 1
        assert result[0].event_type == "created"

    def test_asset_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetAssetHistoryQueryHandler(asset_repo=repo)

        with pytest.raises(HistoryNotFoundError):
            handler.handle(GetAssetHistoryQuery(asset_id="bad", company_id="comp1"))


class TestMyEquipmentQuery:
    def test_returns_assigned_assets(self):
        assets = [_make_asset(serial_number=f"SN{i}") for i in range(2)]
        for a in assets:
            a.assign(user_id="user1")
        repo = MagicMock()
        repo.find_by_assigned_to.return_value = assets
        handler = MyEquipmentQueryHandler(asset_repo=repo)

        result = handler.handle(MyEquipmentQuery(user_id="user1", company_id="comp1"))

        assert len(result) == 2
        assert all(a.status == AssetStatus.ASSIGNED for a in result)
        repo.find_by_assigned_to.assert_called_once_with("user1", "comp1")
