"""Integration tests for /api/v1/auth/api-keys endpoints."""

import pytest


class TestApiKeysEndpoints:
    def test_create_api_key(self, client, auth_as, employee_user):
        """POST /api/v1/auth/api-keys creates API key with raw_key."""
        auth_as(employee_user)

        resp = client.post("/api/v1/auth/api-keys", json={"name": "Test Key"})

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Test Key"
        assert data["raw_key"].startswith("dsm_")
        assert len(data["raw_key"]) == 44
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_api_key_returns_key_once(self, client, auth_as, employee_user):
        """POST returns raw_key but GET list does NOT contain raw_key field."""
        auth_as(employee_user)

        # Create key - should return raw_key
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "Secret Key"})
        assert create_resp.status_code == 201
        assert "raw_key" in create_resp.json()["data"]

        # List keys - raw_key should not be present
        list_resp = client.get("/api/v1/auth/api-keys")
        assert list_resp.status_code == 200
        keys = list_resp.json()["data"]
        assert len(keys) == 1
        assert "raw_key" not in keys[0]
        assert keys[0]["name"] == "Secret Key"

    def test_list_api_keys(self, client, auth_as, employee_user):
        """GET /api/v1/auth/api-keys returns list of API keys without raw_key or key_hash."""
        auth_as(employee_user)

        # Create 2 keys
        client.post("/api/v1/auth/api-keys", json={"name": "Key 1"})
        client.post("/api/v1/auth/api-keys", json={"name": "Key 2"})

        resp = client.get("/api/v1/auth/api-keys")

        assert resp.status_code == 200
        keys = resp.json()["data"]
        assert len(keys) == 2
        # Verify structure of each key
        for key in keys:
            assert "id" in key
            assert "name" in key
            assert "created_at" in key
            assert "is_active" in key
            assert "last_used_at" in key
            assert "raw_key" not in key
            assert "key_hash" not in key

    def test_list_api_keys_empty(self, client, auth_as, employee_user):
        """GET /api/v1/auth/api-keys returns empty list when no keys exist."""
        auth_as(employee_user)

        resp = client.get("/api/v1/auth/api-keys")

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_revoke_api_key(self, client, auth_as, employee_user):
        """DELETE /api/v1/auth/api-keys/{key_id} revokes key (sets is_active=False)."""
        auth_as(employee_user)

        # Create key
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "To Revoke"})
        key_id = create_resp.json()["data"]["id"]

        # Revoke it
        delete_resp = client.delete(f"/api/v1/auth/api-keys/{key_id}")
        assert delete_resp.status_code == 204

        # Verify key is inactive
        list_resp = client.get("/api/v1/auth/api-keys")
        keys = list_resp.json()["data"]
        assert len(keys) == 1
        assert keys[0]["is_active"] is False

    def test_revoke_nonexistent_key(self, client, auth_as, employee_user):
        """DELETE with random key_id returns 404."""
        auth_as(employee_user)

        resp = client.delete("/api/v1/auth/api-keys/01HWKX4T6QRANDOMRANDOM1234")

        assert resp.status_code == 404
        assert "API key not found" in resp.json()["error"]["message"]

    def test_revoke_already_revoked(self, client, auth_as, employee_user):
        """DELETE twice on same key: first 204, second 409."""
        auth_as(employee_user)

        # Create key
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "Double Revoke"})
        key_id = create_resp.json()["data"]["id"]

        # First revoke
        first_resp = client.delete(f"/api/v1/auth/api-keys/{key_id}")
        assert first_resp.status_code == 204

        # Second revoke
        second_resp = client.delete(f"/api/v1/auth/api-keys/{key_id}")
        assert second_resp.status_code == 409
        assert "already revoked" in second_resp.json()["error"]["message"]

    def test_max_10_keys(self, client, auth_as, employee_user):
        """Creating 10 keys succeeds, 11th returns 409."""
        auth_as(employee_user)

        # Create 10 keys - all should succeed
        for i in range(10):
            resp = client.post("/api/v1/auth/api-keys", json={"name": f"Key {i+1}"})
            assert resp.status_code == 201

        # 11th should fail
        resp = client.post("/api/v1/auth/api-keys", json={"name": "Key 11"})
        assert resp.status_code == 409

    def test_tenant_isolation(self, client, auth_as, employee_user, make_user, company):
        """User cannot revoke another user's API key in same company."""
        # Create key as employee_user
        auth_as(employee_user)
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "User 1 Key"})
        key_id = create_resp.json()["data"]["id"]

        # Create second user in same company
        second_user = make_user("user2@testco.com", company_id=company.id)

        # Auth as second user and try to delete first user's key
        auth_as(second_user)
        delete_resp = client.delete(f"/api/v1/auth/api-keys/{key_id}")

        assert delete_resp.status_code == 404

    def test_unauthenticated_rejected(self, client):
        """Requests without authentication should fail with 401."""
        # POST without auth
        resp = client.post("/api/v1/auth/api-keys", json={"name": "Test"})
        assert resp.status_code == 401

        # GET without auth
        resp = client.get("/api/v1/auth/api-keys")
        assert resp.status_code == 401

        # DELETE without auth
        resp = client.delete("/api/v1/auth/api-keys/01HWKX4T6QRANDOMRANDOM1234")
        assert resp.status_code == 401
