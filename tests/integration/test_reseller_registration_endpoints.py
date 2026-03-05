"""Integration tests for reseller registration, approval, login, and password flows."""
from unittest.mock import patch

import pytest

from adapters.http.api.reseller.dependencies import get_current_reseller
from core.password import PasswordService
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def pending_reseller(db_session):
    """Create a pending reseller with password."""
    pw_service = PasswordService()
    r = Reseller.create(
        email="pending@reseller.com",
        name="Pending Partner",
        commission_pct=20,
        min_payout_cents=5000,
        status=ResellerStatus.PENDING,
        password_hash=pw_service.hash_password("password123"),
        company_name="Pending Corp",
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def active_reseller_with_pw(db_session):
    """Create an active reseller with password."""
    pw_service = PasswordService()
    r = Reseller.create(
        email="active@reseller.com",
        name="Active Partner",
        commission_pct=20,
        min_payout_cents=5000,
        password_hash=pw_service.hash_password("password123"),
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


class TestResellerRegistration:
    @patch("src.reseller_bc.reseller.application.commands.register_reseller.send_reseller_registration_confirmation")
    @patch("src.reseller_bc.reseller.application.commands.register_reseller.send_reseller_admin_notification")
    def test_register_success(self, mock_admin, mock_confirm, client, db_session):
        resp = client.post("/api/v1/reseller/auth/register", json={
            "name": "New Partner",
            "email": "new@reseller.com",
            "company_name": "New Corp",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        mock_confirm.delay.assert_called_once()
        mock_admin.delay.assert_called_once()

        # Verify reseller was created as PENDING
        repo = ResellerRepository(db_session)
        reseller = repo.find_by_email("new@reseller.com")
        assert reseller is not None
        assert reseller.status == ResellerStatus.PENDING
        assert reseller.password_hash is not None

    def test_register_duplicate_email(self, client, pending_reseller):
        resp = client.post("/api/v1/reseller/auth/register", json={
            "name": "Duplicate",
            "email": "pending@reseller.com",
            "company_name": "Corp",
            "password": "securepass123",
        })
        assert resp.status_code == 409

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/reseller/auth/register", json={
            "name": "Test",
            "email": "test@reseller.com",
            "company_name": "Corp",
            "password": "short",
        })
        assert resp.status_code == 422


class TestResellerPasswordLogin:
    def test_login_success(self, client, active_reseller_with_pw):
        resp = client.post("/api/v1/reseller/auth/login", json={
            "email": "active@reseller.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]

    def test_login_wrong_password(self, client, active_reseller_with_pw):
        resp = client.post("/api/v1/reseller/auth/login", json={
            "email": "active@reseller.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_pending_blocked(self, client, pending_reseller):
        resp = client.post("/api/v1/reseller/auth/login", json={
            "email": "pending@reseller.com",
            "password": "password123",
        })
        assert resp.status_code == 403
        assert "pending" in resp.json()["detail"].lower()

    def test_login_unknown_email(self, client):
        resp = client.post("/api/v1/reseller/auth/login", json={
            "email": "unknown@reseller.com",
            "password": "password123",
        })
        assert resp.status_code == 401


class TestResellerApproveReject:
    @patch("src.reseller_bc.reseller.application.commands.approve_reseller.send_reseller_approval_email")
    def test_approve_success(self, mock_email, client, pending_reseller, admin_user, auth_as):
        auth_as(admin_user)
        resp = client.post(f"/api/v1/admin/resellers/{pending_reseller.id}/approve")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "active"
        mock_email.delay.assert_called_once()

    @patch("src.reseller_bc.reseller.application.commands.reject_reseller.send_reseller_rejection_email")
    def test_reject_success(self, mock_email, client, pending_reseller, admin_user, auth_as):
        auth_as(admin_user)
        resp = client.post(
            f"/api/v1/admin/resellers/{pending_reseller.id}/reject",
            json={"reason": "Not suitable"},
        )
        assert resp.status_code == 200
        mock_email.delay.assert_called_once()

    def test_approve_requires_super_admin(self, client, pending_reseller):
        resp = client.post(f"/api/v1/admin/resellers/{pending_reseller.id}/approve")
        assert resp.status_code in (401, 403)


class TestResellerForgotResetPassword:
    def test_forgot_password(self, client, active_reseller_with_pw):
        with patch("src.reseller_bc.reseller.application.commands.forgot_password.send_reseller_password_reset_email") as mock_email:
            resp = client.post("/api/v1/reseller/auth/forgot-password", json={
                "email": "active@reseller.com",
            })
            assert resp.status_code == 200
            mock_email.delay.assert_called_once()

    def test_forgot_password_unknown_email_no_error(self, client):
        resp = client.post("/api/v1/reseller/auth/forgot-password", json={
            "email": "unknown@reseller.com",
        })
        assert resp.status_code == 200

    def test_reset_password(self, client, db_session, active_reseller_with_pw):
        from datetime import datetime, timedelta, timezone

        # Set reset token
        repo = ResellerRepository(db_session)
        reseller = repo.find_by_email("active@reseller.com")
        reseller.set_reset_token("test-reset-token", datetime.now(timezone.utc) + timedelta(hours=1))
        repo.save(reseller)
        db_session.flush()

        resp = client.post("/api/v1/reseller/auth/reset-password", json={
            "token": "test-reset-token",
            "password": "newpassword123",
        })
        assert resp.status_code == 200

        # Verify can login with new password
        resp = client.post("/api/v1/reseller/auth/login", json={
            "email": "active@reseller.com",
            "password": "newpassword123",
        })
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        resp = client.post("/api/v1/reseller/auth/reset-password", json={
            "token": "bad-token",
            "password": "newpassword123",
        })
        assert resp.status_code == 400


class TestResellerChangePassword:
    def test_change_password(self, client, active_reseller_with_pw):
        def _override():
            return active_reseller_with_pw
        client.app.dependency_overrides[get_current_reseller] = _override

        resp = client.post("/api/v1/reseller/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client, active_reseller_with_pw):
        def _override():
            return active_reseller_with_pw
        client.app.dependency_overrides[get_current_reseller] = _override

        resp = client.post("/api/v1/reseller/change-password", json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 400
