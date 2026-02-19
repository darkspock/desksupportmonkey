import pytest

from src.mcp_bc.server.domain.entities import ApiKey, ApiKeyAlreadyRevokedError


class TestApiKey:
    def test_api_key_create(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="My API Key",
        )

        assert key.id
        assert len(key.id) == 26  # ULID length
        assert key.user_id == "user123"
        assert key.key_hash == "hash_value"
        assert key.name == "My API Key"
        assert key.is_active is True
        assert key.created_at is None
        assert key.last_used_at is None

    def test_api_key_create_generates_ulid(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="Test",
        )

        assert len(key.id) == 26

    def test_api_key_create_custom_id(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="Test",
            id="custom_id_123",
        )

        assert key.id == "custom_id_123"

    def test_api_key_create_strips_name(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="  Spaced Name  ",
        )

        assert key.name == "Spaced Name"

    def test_api_key_create_empty_name_raises(self):
        with pytest.raises(ValueError, match="API key name is required"):
            ApiKey.create(
                user_id="user123",
                key_hash="hash_value",
                name="",
            )

    def test_api_key_create_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="API key name is required"):
            ApiKey.create(
                user_id="user123",
                key_hash="hash_value",
                name="   ",
            )

    def test_api_key_create_name_too_long_raises(self):
        long_name = "a" * 101
        with pytest.raises(ValueError, match="API key name must be 100 characters or less"):
            ApiKey.create(
                user_id="user123",
                key_hash="hash_value",
                name=long_name,
            )

    def test_api_key_revoke(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="Test",
        )

        assert key.is_active is True
        key.revoke()
        assert key.is_active is False

    def test_api_key_revoke_already_revoked_raises(self):
        key = ApiKey.create(
            user_id="user123",
            key_hash="hash_value",
            name="Test",
        )

        key.revoke()
        with pytest.raises(ApiKeyAlreadyRevokedError, match="is already revoked"):
            key.revoke()
