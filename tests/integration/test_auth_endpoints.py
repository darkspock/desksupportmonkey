"""Integration tests for /api/v1/auth endpoints (mixed auth)."""

import pytest
from unittest.mock import patch, MagicMock


class TestRequestMagicLink:
    @patch("core.email.get_email_service")
    def test_request_magic_link(self, mock_email, client, admin_user, company):
        """Request magic link for an existing user."""
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/auth/magic-link", json={"email": admin_user.email})

        assert resp.status_code == 200
        assert "Magic link sent" in resp.json()["data"]["message"]

    @patch("core.email.get_email_service")
    def test_magic_link_unregistered_domain(self, mock_email, client):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/auth/magic-link", json={"email": "user@unknown.com"})

        assert resp.status_code == 403


class TestVerifyMagicLink:
    def test_verify_invalid_token(self, client):
        resp = client.post("/api/v1/auth/verify", json={"token": "invalid-token"})

        assert resp.status_code == 401

    @patch("core.email.get_email_service")
    def test_verify_valid_token(self, mock_email, client, db_session, admin_user, company):
        """Create a magic link, then verify it."""
        mock_email.return_value = MagicMock()
        from src.auth_bc.magic_link.domain.entities import MagicLink
        from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository

        ml = MagicLink.create(email=admin_user.email)
        MagicLinkRepository(db_session).save(ml)
        db_session.flush()

        resp = client.post("/api/v1/auth/verify", json={"token": ml.token})

        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]


class TestPasswordLogin:
    def test_login_no_password(self, client, admin_user):
        """Admin without password set should fail."""
        resp = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "somepassword",
        })

        assert resp.status_code == 401

    def test_login_with_password(self, client, auth_as, admin_user, db_session):
        """Set password then login."""
        from core.password import PasswordService
        from src.auth_bc.user.infrastructure.repository import UserRepository

        admin_user.set_password_hash(PasswordService.hash_password("StrongPass123"))
        UserRepository(db_session).save(admin_user)
        db_session.flush()

        resp = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "StrongPass123",
        })

        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_login_wrong_password(self, client, admin_user, db_session):
        from core.password import PasswordService
        from src.auth_bc.user.infrastructure.repository import UserRepository

        admin_user.set_password_hash(PasswordService.hash_password("CorrectPass"))
        UserRepository(db_session).save(admin_user)
        db_session.flush()

        resp = client.post("/api/v1/auth/login", json={
            "email": admin_user.email,
            "password": "WrongPass",
        })

        assert resp.status_code == 401


class TestSetPassword:
    def test_set_password(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/auth/set-password", json={"password": "NewStrongPass1"})

        assert resp.status_code == 200
        assert "Password set" in resp.json()["data"]["message"]

    def test_set_password_weak(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/auth/set-password", json={"password": "short"})

        assert resp.status_code == 422

    def test_set_password_non_admin(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.post("/api/v1/auth/set-password", json={"password": "StrongPass123"})

        assert resp.status_code == 403


class TestGetMe:
    def test_get_me(self, client, auth_as, admin_user, company):
        auth_as(admin_user)

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == admin_user.email
        assert data["role"] == "admin"
        assert data["company_name"] == company.name
