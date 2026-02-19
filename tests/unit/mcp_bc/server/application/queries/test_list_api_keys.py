from unittest.mock import MagicMock

from src.mcp_bc.server.application.queries.list_api_keys import (
    ListApiKeysQuery,
    ListApiKeysQueryHandler,
)
from src.mcp_bc.server.domain.entities import ApiKey


class TestListApiKeysQuery:
    def test_list_returns_keys(self):
        key1 = ApiKey(
            id="key1",
            user_id="user1",
            key_hash="hash1",
            name="Key 1",
            is_active=True,
        )
        key2 = ApiKey(
            id="key2",
            user_id="user1",
            key_hash="hash2",
            name="Key 2",
            is_active=False,
        )
        repo = MagicMock()
        repo.find_all_by_user.return_value = [key1, key2]
        handler = ListApiKeysQueryHandler(api_key_repo=repo)

        result = handler.handle(ListApiKeysQuery(user_id="user1"))

        assert len(result) == 2
        assert result[0] == key1
        assert result[1] == key2
        repo.find_all_by_user.assert_called_once_with("user1")

    def test_list_empty(self):
        repo = MagicMock()
        repo.find_all_by_user.return_value = []
        handler = ListApiKeysQueryHandler(api_key_repo=repo)

        result = handler.handle(ListApiKeysQuery(user_id="user1"))

        assert result == []
        repo.find_all_by_user.assert_called_once_with("user1")
