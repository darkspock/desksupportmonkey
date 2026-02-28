"""Integration tests for onboarding wizard endpoints."""

import pytest


class TestOnboardingStatus:
    def test_get_status_needs_onboarding(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/my/onboarding/status")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["needs_onboarding"] is True
        assert data["sector"] is None
        assert data["onboarding_completed_at"] is None

    def test_get_status_after_completion(self, client, auth_as, admin_user):
        auth_as(admin_user)

        client.post("/api/v1/my/onboarding/complete", json={"sector": "technology"})

        resp = client.get("/api/v1/my/onboarding/status")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["needs_onboarding"] is False
        assert data["sector"] == "technology"
        assert data["onboarding_completed_at"] is not None

    def test_get_status_forbidden_for_technician(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/my/onboarding/status")

        assert resp.status_code == 403


class TestCompleteOnboarding:
    def test_complete_with_valid_sector(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/my/onboarding/complete", json={"sector": "financial_services"})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["sector"] == "financial_services"
        assert data["onboarding_completed_at"] is not None
        assert data["needs_onboarding"] is False

    def test_complete_with_null_sector_skip(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/my/onboarding/complete", json={"sector": None})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["sector"] is None
        assert data["onboarding_completed_at"] is not None
        assert data["needs_onboarding"] is False

    def test_complete_with_invalid_sector(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/my/onboarding/complete", json={"sector": "invalid_sector"})

        assert resp.status_code == 422

    def test_complete_forbidden_for_technician(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.post("/api/v1/my/onboarding/complete", json={"sector": "technology"})

        assert resp.status_code == 403


class TestCompanySettingsWithSector:
    def test_get_includes_sector(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/my/company-settings")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "sector" in data
        assert data["sector"] is None

    def test_put_updates_sector(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.put("/api/v1/my/company-settings", json={
            "email_domains": ["testco.com"],
            "sector": "healthcare",
        })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["sector"] == "healthcare"

    def test_put_invalid_sector_returns_422(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.put("/api/v1/my/company-settings", json={
            "email_domains": ["testco.com"],
            "sector": "totally_fake",
        })

        assert resp.status_code == 422


class TestMeNeedsOnboarding:
    def test_admin_needs_onboarding_true(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["needs_onboarding"] is True

    def test_admin_after_onboarding_false(self, client, auth_as, admin_user):
        auth_as(admin_user)

        client.post("/api/v1/my/onboarding/complete", json={"sector": "technology"})

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["needs_onboarding"] is False

    def test_technician_always_false(self, client, auth_as, technician_user):
        auth_as(technician_user)

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["needs_onboarding"] is False
