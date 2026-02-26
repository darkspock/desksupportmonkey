from unittest.mock import MagicMock

from src.asset_bc.checkout.application.queries.list_my_custody_history import (
    ListMyCustodyHistoryQuery,
    ListMyCustodyHistoryQueryHandler,
)
from src.asset_bc.checkout.domain.entities import AssetCheckout
from src.asset_bc.checkout.domain.enums import AssetCondition


def _make_checkout(**overrides):
    defaults = dict(
        company_id="comp1",
        asset_id="asset1",
        user_id="user1",
        checked_out_by="tech1",
        condition_out=AssetCondition.GOOD,
    )
    defaults.update(overrides)
    co = AssetCheckout.create(**defaults)
    co.checkin(checked_in_by="tech1", condition_in=AssetCondition.GOOD)
    return co


class TestListMyCustodyHistory:
    def test_returns_dtos_and_total(self):
        co1 = _make_checkout(asset_id="a1")
        co2 = _make_checkout(asset_id="a2")
        repo = MagicMock()
        repo.find_history_by_user.return_value = ([co1, co2], 2)

        handler = ListMyCustodyHistoryQueryHandler(checkout_repo=repo)
        dtos, total = handler.handle(
            ListMyCustodyHistoryQuery(user_id="user1", company_id="comp1")
        )

        assert total == 2
        assert len(dtos) == 2
        assert dtos[0].asset_id == "a1"
        assert dtos[1].asset_id == "a2"
        assert dtos[0].checked_in_at is not None

    def test_empty_history(self):
        repo = MagicMock()
        repo.find_history_by_user.return_value = ([], 0)

        handler = ListMyCustodyHistoryQueryHandler(checkout_repo=repo)
        dtos, total = handler.handle(
            ListMyCustodyHistoryQuery(user_id="user1", company_id="comp1")
        )

        assert total == 0
        assert dtos == []

    def test_passes_pagination(self):
        repo = MagicMock()
        repo.find_history_by_user.return_value = ([], 0)

        handler = ListMyCustodyHistoryQueryHandler(checkout_repo=repo)
        handler.handle(
            ListMyCustodyHistoryQuery(
                user_id="user1", company_id="comp1", page=3, page_size=10
            )
        )

        repo.find_history_by_user.assert_called_once_with(
            "user1", "comp1", page=3, page_size=10
        )
