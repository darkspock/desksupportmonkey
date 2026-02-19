from unittest.mock import MagicMock

import pytest

from src.mcp_bc.server.application.commands.create_api_key import (
    CreateApiKeyCommand,
    CreateApiKeyCommandHandler,
    MaxApiKeysReachedError,
    generate_api_key,
)


class TestCreateApiKeyCommand:
    def test_create_api_key_success(self):
        repo = MagicMock()
        repo.count_active_by_user.return_value = 0
        handler = CreateApiKeyCommandHandler(api_key_repo=repo)

        handler.handle(
            CreateApiKeyCommand(
                user_id="user123",
                name="Test Key",
                key_hash="hash_value",
            )
        )

        repo.save.assert_called_once()
        repo.count_active_by_user.assert_called_once_with("user123")

    def test_create_api_key_max_reached(self):
        repo = MagicMock()
        repo.count_active_by_user.return_value = 10
        handler = CreateApiKeyCommandHandler(api_key_repo=repo)

        with pytest.raises(MaxApiKeysReachedError, match="Maximum 10 active API keys allowed"):
            handler.handle(
                CreateApiKeyCommand(
                    user_id="user123",
                    name="Test Key",
                    key_hash="hash_value",
                )
            )

        repo.save.assert_not_called()

    def test_create_api_key_at_limit_minus_one(self):
        repo = MagicMock()
        repo.count_active_by_user.return_value = 9
        handler = CreateApiKeyCommandHandler(api_key_repo=repo)

        handler.handle(
            CreateApiKeyCommand(
                user_id="user123",
                name="Test Key",
                key_hash="hash_value",
            )
        )

        repo.save.assert_called_once()

    def test_generate_api_key_format(self):
        raw_key, key_hash = generate_api_key()

        assert raw_key.startswith("dsm_")
        assert len(raw_key) == 44  # dsm_ (4) + 40 hex chars
        assert isinstance(key_hash, str)
        assert len(key_hash) > 0

    def test_generate_api_key_unique(self):
        raw_key1, hash1 = generate_api_key()
        raw_key2, hash2 = generate_api_key()

        assert raw_key1 != raw_key2
        assert hash1 != hash2
