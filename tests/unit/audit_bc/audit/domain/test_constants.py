from src.audit_bc.audit.domain.constants import (
    SANITIZED_FIELDS,
    sanitize_request_data,
)


class TestSanitizedFields:
    def test_contains_expected_fields(self):
        expected = {
            "password", "password_hash", "token", "magic_link",
            "secret", "stripe_secret_key", "credentials",
            "current_password", "new_password",
        }
        assert SANITIZED_FIELDS == expected


class TestSanitizeRequestData:
    def test_redacts_password(self):
        data = {"email": "a@b.com", "password": "secret123"}
        result = sanitize_request_data(data)
        assert result["email"] == "a@b.com"
        assert result["password"] == "[REDACTED]"

    def test_redacts_token(self):
        data = {"token": "abc123", "name": "test"}
        result = sanitize_request_data(data)
        assert result["token"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_redacts_nested(self):
        data = {
            "user": {
                "email": "a@b.com",
                "password_hash": "hashed",
            },
            "action": "create",
        }
        result = sanitize_request_data(data)
        assert result["user"]["email"] == "a@b.com"
        assert result["user"]["password_hash"] == "[REDACTED]"
        assert result["action"] == "create"

    def test_preserves_safe_fields(self):
        data = {"name": "Test", "email": "a@b.com", "status": "active"}
        result = sanitize_request_data(data)
        assert result == data

    def test_none_input(self):
        assert sanitize_request_data(None) is None

    def test_does_not_mutate_original(self):
        data = {"password": "secret"}
        result = sanitize_request_data(data)
        assert data["password"] == "secret"
        assert result["password"] == "[REDACTED]"

    def test_multiple_sensitive_fields(self):
        data = {
            "password": "p",
            "current_password": "cp",
            "new_password": "np",
            "stripe_secret_key": "sk",
            "magic_link": "ml",
            "credentials": "creds",
            "safe": "ok",
        }
        result = sanitize_request_data(data)
        assert result["password"] == "[REDACTED]"
        assert result["current_password"] == "[REDACTED]"
        assert result["new_password"] == "[REDACTED]"
        assert result["stripe_secret_key"] == "[REDACTED]"
        assert result["magic_link"] == "[REDACTED]"
        assert result["credentials"] == "[REDACTED]"
        assert result["safe"] == "ok"
