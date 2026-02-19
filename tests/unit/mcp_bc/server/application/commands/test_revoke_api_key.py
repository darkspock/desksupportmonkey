from unittest.mock import MagicMock

import pytest

from src.mcp_bc.server.application.commands.revoke_api_key import (
    RevokeApiKeyCommand,
    RevokeApiKeyCommandHandler,
    ApiKeyNotFoundError,
)
from src.mcp_bc.server.domain.entities import ApiKey, ApiKeyAlreadyRevokedError


class TestRevokeApiKeyCommand:
    def test_revoke_success(self):
        key = ApiKey(
            id="key1",
            user_id="user1",
            key_hash="hash",
            name="test",
            is_active=True,
        )
        repo = MagicMock()
        repo.find_by_id.return_value = key
        handler = RevokeApiKeyCommandHandler(api_key_repo=repo)

        handler.handle(
            RevokeApiKeyCommand(
                key_id="key1",
                user_id="user1",
            )
        )

        assert key.is_active is False
        repo.save.assert_called_once_with(key)

    def test_revoke_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = RevokeApiKeyCommandHandler(api_key_repo=repo)

        with pytest.raises(ApiKeyNotFoundError, match="API key 'key1' not found"):
            handler.handle(
                RevokeApiKeyCommand(
                    key_id="key1",
                    user_id="user1",
                )
            )

        repo.save.assert_not_called()

    def test_revoke_already_revoked(self):
        key = ApiKey(
            id="key1",
            user_id="user1",
            key_hash="hash",
            name="test",
            is_active=False,
        )
        repo = MagicMock()
        repo.find_by_id.return_value = key
        handler = RevokeApiKeyCommandHandler(api_key_repo=repo)

        with pytest.raises(ApiKeyAlreadyRevokedError, match="is already revoked"):
            handler.handle(
                RevokeApiKeyCommand(
                    key_id="key1",
                    user_id="user1",
                )
            )

        repo.save.assert_not_called()
