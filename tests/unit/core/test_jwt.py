import pytest

from core.jwt import JWTService, InvalidTokenError, ExpiredTokenError


class TestJWTService:
    def setup_method(self):
        self.svc = JWTService(secret="test-secret", algorithm="HS256", expire_hours=24)

    def test_create_and_decode_token(self):
        token = self.svc.create_token(user_id="user123", company_id="comp456", role="admin")
        payload = self.svc.decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["company_id"] == "comp456"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        with pytest.raises(InvalidTokenError):
            self.svc.decode_token("not.a.valid.token")

    def test_decode_expired_token(self):
        svc = JWTService(secret="test-secret", expire_hours=0)
        token = svc.create_token(user_id="user123", company_id=None, role="employee")
        # Token with 0 hours expiry should be expired immediately
        # But since creation and decode happen nearly instantly, we test with a negative value
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone
        payload = {
            "sub": "user123",
            "company_id": None,
            "role": "employee",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }
        expired_token = pyjwt.encode(payload, "test-secret", algorithm="HS256")
        with pytest.raises(ExpiredTokenError):
            self.svc.decode_token(expired_token)

    def test_null_company_id(self):
        token = self.svc.create_token(user_id="user123", company_id=None, role="super_admin")
        payload = self.svc.decode_token(token)
        assert payload["company_id"] is None
