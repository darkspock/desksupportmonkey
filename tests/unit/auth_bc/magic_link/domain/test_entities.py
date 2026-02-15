from datetime import datetime, timedelta, timezone

from src.auth_bc.magic_link.domain.entities import MagicLink


class TestMagicLink:
    def test_create(self):
        ml = MagicLink.create(email="test@example.com")
        assert ml.email == "test@example.com"
        assert len(ml.token) > 0
        assert ml.used_at is None
        assert ml.expires_at > datetime.now(timezone.utc)
        assert len(ml.id) == 26

    def test_create_normalizes_email(self):
        ml = MagicLink.create(email="  TEST@Example.COM  ")
        assert ml.email == "test@example.com"

    def test_create_custom_ttl(self):
        ml = MagicLink.create(email="test@example.com", ttl_hours=1)
        expected_max = datetime.now(timezone.utc) + timedelta(hours=1, seconds=5)
        expected_min = datetime.now(timezone.utc) + timedelta(hours=1, seconds=-5)
        assert expected_min <= ml.expires_at <= expected_max

    def test_unique_tokens(self):
        ml1 = MagicLink.create(email="test@example.com")
        ml2 = MagicLink.create(email="test@example.com")
        assert ml1.token != ml2.token

    def test_is_expired_false_when_fresh(self):
        ml = MagicLink.create(email="test@example.com")
        assert ml.is_expired() is False

    def test_is_expired_true_when_past(self):
        ml = MagicLink.create(email="test@example.com")
        ml.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert ml.is_expired() is True

    def test_is_used_false_when_fresh(self):
        ml = MagicLink.create(email="test@example.com")
        assert ml.is_used() is False

    def test_mark_used(self):
        ml = MagicLink.create(email="test@example.com")
        assert ml.is_used() is False
        ml.mark_used()
        assert ml.is_used() is True
        assert ml.used_at is not None
