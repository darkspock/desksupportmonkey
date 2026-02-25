"""Integration tests for /api/v1/settings/nav-visibility."""

import pytest


class TestGetNavVisibility:
    def test_get_returns_null_when_no_config(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/settings/nav-visibility")
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_get_returns_saved_config(self, client, auth_as, admin_user):
        auth_as(admin_user)
        # Save first
        client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"employee": ["/my/shipments"]}},
        )
        # Then get
        resp = client.get("/api/v1/settings/nav-visibility")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"] == {"employee": ["/my/shipments"]}
        assert data["company_id"] == admin_user.company_id


class TestSaveNavVisibility:
    def test_save_creates_config(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/nav-visibility",
            json={
                "hidden_nav_items": {
                    "employee": ["/my/shipments", "/my/incidents"],
                    "technician": ["/vendors"],
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"]["employee"] == ["/my/shipments", "/my/incidents"]
        assert data["hidden_nav_items"]["technician"] == ["/vendors"]

    def test_save_updates_existing(self, client, auth_as, admin_user):
        auth_as(admin_user)
        # Create
        client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"employee": ["/my/shipments"]}},
        )
        # Update
        resp = client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"technician": ["/vendors"]}},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "employee" not in data["hidden_nav_items"]
        assert data["hidden_nav_items"]["technician"] == ["/vendors"]

    def test_save_accepts_admin_role(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"admin": ["/some/path"]}},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"]["admin"] == ["/some/path"]

    def test_save_empty_clears(self, client, auth_as, admin_user):
        auth_as(admin_user)
        # Create first
        client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"employee": ["/my/shipments"]}},
        )
        # Clear
        resp = client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {}},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"] == {}


class TestPermissions:
    def test_technician_cannot_access(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.get("/api/v1/settings/nav-visibility")
        assert resp.status_code == 403

    def test_technician_cannot_save(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {}},
        )
        assert resp.status_code == 403

    def test_employee_cannot_access(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.get("/api/v1/settings/nav-visibility")
        assert resp.status_code == 403


class TestAuthMeIncludesNavConfig:
    def test_auth_me_includes_hidden_nav_items_when_set(
        self, client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        # Save nav config
        client.put(
            "/api/v1/settings/nav-visibility",
            json={"hidden_nav_items": {"employee": ["/my/shipments"]}},
        )
        # Check /auth/me
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"] == {"employee": ["/my/shipments"]}

    def test_auth_me_returns_null_when_no_config(
        self, client, auth_as, employee_user,
    ):
        auth_as(employee_user)
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["hidden_nav_items"] is None
