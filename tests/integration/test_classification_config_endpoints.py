"""Integration tests for /api/v1/settings/request-classification."""


class TestClassificationConfig:
    def test_save_and_get_config(self, client, auth_as, admin_user):
        auth_as(admin_user)

        # Save
        resp = client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": True,
                "provider": "openai",
                "model": "gpt-4o-mini",
                "confidence_threshold": 0.8,
                "prompt_template": "Be precise with classification.",
                "timeout_seconds": 15,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["is_enabled"] is True
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o-mini"
        assert data["confidence_threshold"] == 0.8
        assert data["prompt_template"] == "Be precise with classification."
        assert data["timeout_seconds"] == 15

        # Get
        resp = client.get("/api/v1/settings/request-classification")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "openai"
        assert data["is_enabled"] is True

    def test_update_config(self, client, auth_as, admin_user):
        auth_as(admin_user)

        # Create
        client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": True,
                "provider": "openai",
                "confidence_threshold": 0.7,
                "timeout_seconds": 10,
            },
        )

        # Update
        resp = client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": False,
                "provider": "groq",
                "confidence_threshold": 0.9,
                "timeout_seconds": 30,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "groq"
        assert data["is_enabled"] is False
        assert data["confidence_threshold"] == 0.9
        assert data["timeout_seconds"] == 30

    def test_invalid_provider(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": True,
                "provider": "invalid_provider",
                "confidence_threshold": 0.7,
                "timeout_seconds": 10,
            },
        )
        assert resp.status_code == 422

    def test_invalid_threshold(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": True,
                "provider": "openai",
                "confidence_threshold": 0.3,
                "timeout_seconds": 10,
            },
        )
        assert resp.status_code == 422

    def test_get_config_empty(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/settings/request-classification")
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_employee_forbidden_put(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.put(
            "/api/v1/settings/request-classification",
            json={
                "is_enabled": True,
                "provider": "openai",
                "confidence_threshold": 0.7,
                "timeout_seconds": 10,
            },
        )
        assert resp.status_code == 403

    def test_employee_forbidden_get(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.get("/api/v1/settings/request-classification")
        assert resp.status_code == 403
