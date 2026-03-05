"""Integration tests for admin reseller CRUD endpoints."""
import pytest


class TestAdminResellerEndpoints:
    """Tests for /api/v1/admin/resellers endpoints."""

    def test_create_reseller(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.post("/api/v1/admin/resellers/", json={
            "email": "partner@reseller.com",
            "name": "Partner Inc",
            "commission_pct": 20,
            "min_payout_cents": 5000,
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["email"] == "partner@reseller.com"
        assert data["name"] == "Partner Inc"
        assert data["commission_pct"] == 20
        assert data["min_payout_cents"] == 5000
        assert data["status"] == "active"
        assert data["referral_code"]  # auto-generated
        assert data["id"]  # ULID generated

    def test_create_reseller_duplicate_email(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        client.post("/api/v1/admin/resellers/", json={
            "email": "dup@reseller.com",
            "name": "First",
            "commission_pct": 20,
            "min_payout_cents": 5000,
        })
        resp = client.post("/api/v1/admin/resellers/", json={
            "email": "dup@reseller.com",
            "name": "Second",
            "commission_pct": 15,
            "min_payout_cents": 3000,
        })
        assert resp.status_code == 409

    def test_create_reseller_invalid_commission(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.post("/api/v1/admin/resellers/", json={
            "email": "bad@reseller.com",
            "name": "Bad",
            "commission_pct": 150,
            "min_payout_cents": 5000,
        })
        assert resp.status_code == 422

    def test_create_reseller_invalid_min_payout(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.post("/api/v1/admin/resellers/", json={
            "email": "bad2@reseller.com",
            "name": "Bad",
            "commission_pct": 20,
            "min_payout_cents": 0,
        })
        assert resp.status_code == 422

    def test_list_resellers(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        # Create 2 resellers
        client.post("/api/v1/admin/resellers/", json={
            "email": "a@reseller.com", "name": "A", "commission_pct": 10, "min_payout_cents": 1000,
        })
        client.post("/api/v1/admin/resellers/", json={
            "email": "b@reseller.com", "name": "B", "commission_pct": 20, "min_payout_cents": 2000,
        })
        resp = client.get("/api/v1/admin/resellers/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_get_reseller_by_id(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        create_resp = client.post("/api/v1/admin/resellers/", json={
            "email": "get@reseller.com", "name": "Get Test", "commission_pct": 15, "min_payout_cents": 3000,
        })
        reseller_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/admin/resellers/{reseller_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "get@reseller.com"

    def test_get_reseller_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.get("/api/v1/admin/resellers/nonexistent-id")
        assert resp.status_code == 404

    def test_update_reseller_settings(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        create_resp = client.post("/api/v1/admin/resellers/", json={
            "email": "upd@reseller.com", "name": "Update Test", "commission_pct": 20, "min_payout_cents": 5000,
        })
        reseller_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/admin/resellers/{reseller_id}", json={
            "commission_pct": 30,
            "min_payout_cents": 10000,
            "status": "suspended",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["commission_pct"] == 30
        assert data["min_payout_cents"] == 10000
        assert data["status"] == "suspended"

    def test_update_reseller_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.patch("/api/v1/admin/resellers/nonexistent-id", json={
            "commission_pct": 30,
        })
        assert resp.status_code == 404

    def test_non_super_admin_rejected(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get("/api/v1/admin/resellers/")
        assert resp.status_code == 403
