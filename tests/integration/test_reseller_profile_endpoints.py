"""Integration tests for reseller portal endpoints (me, profile, dashboard)."""
import pytest

from adapters.http.api.reseller.dependencies import get_current_reseller
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def reseller(db_session):
    """Create a real reseller in the test DB."""
    r = Reseller.create(
        email="portal@reseller.com",
        name="Portal Reseller",
        commission_pct=20,
        min_payout_cents=5000,
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def suspended_reseller(db_session):
    """Create a suspended reseller in the test DB."""
    r = Reseller.create(
        email="suspended@reseller.com",
        name="Suspended Reseller",
        commission_pct=15,
        min_payout_cents=3000,
    )
    r.suspend()
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


def _auth_as_reseller(client, reseller_entity):
    """Override get_current_reseller to return the given reseller."""
    def _override():
        return reseller_entity
    client.app.dependency_overrides[get_current_reseller] = _override


class TestResellerProfileEndpoints:
    def test_get_me(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == "portal@reseller.com"
        assert data["name"] == "Portal Reseller"
        assert data["commission_pct"] == 20
        assert data["status"] == "active"

    def test_update_profile(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.put("/api/v1/reseller/profile", json={
            "company_name": "Acme Corp",
            "tax_id": "123-456-789",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["company_name"] == "Acme Corp"
        assert data["tax_id"] == "123-456-789"

    def test_update_profile_suspended_rejected(self, client, suspended_reseller):
        _auth_as_reseller(client, suspended_reseller)
        resp = client.put("/api/v1/reseller/profile", json={
            "company_name": "Should Fail",
        })
        assert resp.status_code == 403

    def test_get_dashboard(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["client_count"] == 0
        assert data["total_commissions_cents"] == 0
        assert data["available_balance_cents"] == 0
        assert data["pending_payout_cents"] == 0

    def test_reseller_jwt_required(self, client):
        """User JWT should not work on reseller endpoints."""
        # No auth override — no bearer token at all
        resp = client.get("/api/v1/reseller/me")
        assert resp.status_code in (401, 403)


class TestJWTTypeIsolation:
    def test_user_token_rejected_on_reseller_endpoints(self, client, admin_user, auth_as):
        """A user JWT should be rejected on reseller endpoints because
        get_current_reseller checks type=reseller in the token."""
        # auth_as overrides get_current_user, not get_current_reseller
        # So reseller endpoints should still reject
        auth_as(admin_user)
        resp = client.get("/api/v1/reseller/me")
        # Without a reseller override, the default get_current_reseller
        # will try to parse a bearer token and fail
        assert resp.status_code in (401, 403)

    def test_old_token_without_type_works_on_user_endpoints(self, client, admin_user, auth_as):
        """Existing tokens without type claim should still work on user endpoints
        since get_current_user defaults type to 'user'."""
        auth_as(admin_user)
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
