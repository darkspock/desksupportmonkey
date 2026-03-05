"""Integration tests for slug-scoped auth endpoints and multi-company detection (TASK-031)."""

import pytest
from unittest.mock import patch, MagicMock


class TestSlugScopedMagicLink:
    @patch("core.email.get_email_service")
    def test_scoped_magic_link_success(self, mock_email, client, admin_user, company):
        mock_email.return_value = MagicMock()

        resp = client.post(
            f"/api/v1/auth/{company.slug}/magic-link",
            json={"email": admin_user.email},
        )

        assert resp.status_code == 200
        assert "Magic link sent" in resp.json()["data"]["message"]

    def test_scoped_magic_link_invalid_slug(self, client):
        resp = client.post(
            "/api/v1/auth/nonexistent-slug/magic-link",
            json={"email": "user@example.com"},
        )

        assert resp.status_code == 404

    @patch("core.email.get_email_service")
    def test_scoped_magic_link_email_not_in_company(self, mock_email, client, company):
        mock_email.return_value = MagicMock()

        resp = client.post(
            f"/api/v1/auth/{company.slug}/magic-link",
            json={"email": "user@unknown-domain.com"},
        )

        assert resp.status_code == 403


class TestSlugScopedVerify:
    @patch("core.email.get_email_service")
    def test_scoped_verify_with_membership(self, mock_email, client, db_session, admin_user, company):
        mock_email.return_value = MagicMock()
        from src.auth_bc.magic_link.domain.entities import MagicLink
        from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
        from src.auth_bc.company_user.domain.entities import CompanyUser
        from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
        from src.auth_bc.user.domain.enums import UserRole

        # Create a membership for the user
        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
        )
        CompanyUserRepository(db_session).save(cu)

        # Create a scoped magic link
        ml = MagicLink.create(email=admin_user.email, company_id=company.id)
        MagicLinkRepository(db_session).save(ml)
        db_session.flush()

        resp = client.post(
            f"/api/v1/auth/{company.slug}/verify",
            json={"token": ml.token},
        )

        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_scoped_verify_invalid_slug(self, client):
        resp = client.post(
            "/api/v1/auth/bad-slug/verify",
            json={"token": "some-token"},
        )

        assert resp.status_code == 404


class TestSlugScopedPasswordLogin:
    def test_scoped_login_success(self, client, db_session, admin_user, company):
        from core.password import PasswordService
        from src.auth_bc.user.infrastructure.repository import UserRepository
        from src.auth_bc.company_user.domain.entities import CompanyUser
        from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
        from src.auth_bc.user.domain.enums import UserRole

        admin_user.set_password_hash(PasswordService.hash_password("StrongPass123"))
        UserRepository(db_session).save(admin_user)

        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
        )
        CompanyUserRepository(db_session).save(cu)
        db_session.flush()

        resp = client.post(
            f"/api/v1/auth/{company.slug}/login",
            json={"email": admin_user.email, "password": "StrongPass123"},
        )

        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_scoped_login_invalid_slug(self, client):
        resp = client.post(
            "/api/v1/auth/nonexistent/login",
            json={"email": "admin@testco.com", "password": "pass"},
        )

        assert resp.status_code == 404


class TestMultiCompanyDetection:
    @patch("core.email.get_email_service")
    def test_single_company_proceeds_normally(self, mock_email, client, admin_user, company):
        """Email matching single company proceeds as before."""
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/auth/magic-link", json={"email": admin_user.email})

        assert resp.status_code == 200

    @patch("core.email.get_email_service")
    @patch("adapters.http.api.auth.routers._check_multi_company")
    def test_multi_company_returns_409_via_mock(self, mock_check, mock_email, client, admin_user, company):
        """Multi-company detection returns 409 with slugs (mocked since domain is globally unique)."""
        from fastapi import HTTPException, status
        import json

        mock_email.return_value = MagicMock()
        mock_check.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=json.dumps({"error": "multiple_companies", "slugs": ["test-company", "second-company"]}),
        )

        resp = client.post("/api/v1/auth/magic-link", json={"email": admin_user.email})

        assert resp.status_code == 409
        detail = resp.json()["error"]["message"]
        assert "multiple_companies" in detail


class TestSessionInvalidation:
    def test_jwt_company_id_mismatch_returns_401(self, client, db_session, admin_user, company):
        """JWT with company_id that doesn't match user's current company → 401."""
        from core.jwt import JWTService

        jwt = JWTService()
        # Issue JWT with a different company_id than the user's actual company
        token = jwt.create_token(
            user_id=admin_user.id,
            company_id="wrong-company-id",
            role="admin",
        )

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 401
        assert "Session expired" in resp.json()["error"]["message"]

    def test_super_admin_exempt_from_session_invalidation(self, client, db_session, super_admin_user):
        """SUPER_ADMIN tokens have no company_id — exempt from mismatch check."""
        from core.jwt import JWTService

        jwt = JWTService()
        token = jwt.create_token(
            user_id=super_admin_user.id,
            company_id=None,
            role="super_admin",
        )

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200

    def test_matching_company_id_succeeds(self, client, db_session, admin_user, company):
        """JWT with correct company_id passes session check."""
        from core.jwt import JWTService

        jwt = JWTService()
        token = jwt.create_token(
            user_id=admin_user.id,
            company_id=admin_user.company_id,
            role="admin",
        )

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
