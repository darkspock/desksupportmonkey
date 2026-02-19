"""Integration tests for /api/v1/settings/assignment-ai."""


class TestAssignmentAIConfig:
    def test_save_and_get_config(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)

        # Save
        resp = client.put(
            "/api/v1/settings/assignment-ai",
            json={
                "provider": "openai",
                "prompt_template": "Pick the best asset.",
                "model": "gpt-4o-mini",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "openai"
        assert data["prompt_template"] == "Pick the best asset."
        assert data["model"] == "gpt-4o-mini"

        # Get
        resp = client.get("/api/v1/settings/assignment-ai")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "openai"

    def test_update_config(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)

        # Create
        client.put(
            "/api/v1/settings/assignment-ai",
            json={
                "provider": "openai",
                "prompt_template": "v1",
            },
        )

        # Update
        resp = client.put(
            "/api/v1/settings/assignment-ai",
            json={
                "provider": "groq",
                "prompt_template": "v2",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["provider"] == "groq"
        assert data["prompt_template"] == "v2"

    def test_invalid_provider(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/assignment-ai",
            json={
                "provider": "invalid",
                "prompt_template": "prompt",
            },
        )
        assert resp.status_code == 422

    def test_get_config_empty(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = client.get("/api/v1/settings/assignment-ai")
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_employee_forbidden(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get("/api/v1/settings/assignment-ai")
        assert resp.status_code == 403
