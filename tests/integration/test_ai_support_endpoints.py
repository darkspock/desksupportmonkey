"""Integration tests for POST /api/v1/my/ai-support endpoint."""

from unittest.mock import MagicMock, patch


class TestAISupportEndpoint:
    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_401_without_auth(self, mock_primary, mock_fallback, mock_redis, client):
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 401

    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_403_for_employee(
        self, mock_primary, mock_fallback, mock_redis,
        client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 403

    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_200_success_admin(
        self, mock_primary_fn, mock_fallback_fn, mock_redis_fn,
        client, auth_as, admin_user,
    ):
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "Here is how to do it."
        mock_primary_fn.return_value = mock_provider
        mock_fallback_fn.return_value = MagicMock()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.pipeline.return_value = MagicMock()
        mock_redis_fn.return_value = mock_redis

        auth_as(admin_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "How do I create an asset?"}],
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["response"] == "Here is how to do it."

    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_200_success_technician(
        self, mock_primary_fn, mock_fallback_fn, mock_redis_fn,
        client, auth_as, technician_user,
    ):
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "Response for tech."
        mock_primary_fn.return_value = mock_provider
        mock_fallback_fn.return_value = MagicMock()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.pipeline.return_value = MagicMock()
        mock_redis_fn.return_value = mock_redis

        auth_as(technician_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "Help me"}],
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["response"] == "Response for tech."

    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_429_rate_limit(
        self, mock_primary_fn, mock_fallback_fn, mock_redis_fn,
        client, auth_as, admin_user,
    ):
        mock_primary_fn.return_value = MagicMock()
        mock_fallback_fn.return_value = MagicMock()

        mock_redis = MagicMock()
        mock_redis.get.return_value = "20"
        mock_redis_fn.return_value = mock_redis

        auth_as(admin_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })

        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()

    @patch("adapters.http.api.my.ai_support_router._get_redis")
    @patch("adapters.http.api.my.ai_support_router.get_fallback_provider")
    @patch("adapters.http.api.my.ai_support_router.get_ai_provider")
    def test_503_unavailable(
        self, mock_primary_fn, mock_fallback_fn, mock_redis_fn,
        client, auth_as, admin_user,
    ):
        from src.support_bc.ai_assistant.domain.exceptions import AIProviderError

        mock_provider = MagicMock()
        mock_provider.chat.side_effect = AIProviderError("fail")
        mock_primary_fn.return_value = mock_provider

        mock_fallback = MagicMock()
        mock_fallback.chat.side_effect = AIProviderError("also fail")
        mock_fallback_fn.return_value = mock_fallback

        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_fn.return_value = mock_redis

        auth_as(admin_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })

        assert resp.status_code == 503

    def test_422_empty_messages(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [],
        })
        assert resp.status_code == 422

    def test_422_invalid_role(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.post("/api/v1/my/ai-support", json={
            "messages": [{"role": "system", "content": "Hello"}],
        })
        assert resp.status_code == 422
