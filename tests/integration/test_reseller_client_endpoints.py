"""Integration tests for reseller client management endpoints (F2)."""
import pytest
from unittest.mock import patch

from adapters.http.api.reseller.dependencies import get_current_reseller
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def reseller(db_session):
    """Create an active reseller in the test DB."""
    r = Reseller.create(
        email="clients@reseller.com",
        name="Client Reseller",
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
        email="suspended-client@reseller.com",
        name="Suspended Client Reseller",
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


def _create_reseller_client(db_session, reseller_id, company_id, is_demo=False):
    """Helper to create a ResellerClient directly in the DB."""
    client_entity = ResellerClient.create(
        reseller_id=reseller_id,
        company_id=company_id,
        source=ClientSource.MANUAL,
        is_demo=is_demo,
    )
    ResellerClientRepository(db_session).save(client_entity)
    db_session.flush()
    return client_entity


class TestCreateDemoAccount:
    """Tests for POST /api/v1/reseller/clients/demo."""

    @patch("scripts.seed_demo_data.seed_company_data")
    def test_create_demo_success(self, mock_seed, client, reseller, db_session):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/clients/demo", json={
            "company_name": "Demo Corp Test",
        })
        assert resp.status_code == 201, resp.json()
        data = resp.json()["data"]
        assert data["client_id"]
        assert data["company_id"]
        assert data["company_name"] == "Demo Corp Test (Demo)"
        assert data["admin_email"]
        assert "dsm.local" in data["admin_email"]
        assert data["admin_password"]  # random password returned

    def test_create_demo_suspended_reseller(self, client, suspended_reseller):
        _auth_as_reseller(client, suspended_reseller)
        resp = client.post("/api/v1/reseller/clients/demo", json={
            "company_name": "Should Fail",
        })
        # require_active_reseller dependency rejects suspended resellers
        assert resp.status_code in (401, 403)

    @patch("scripts.seed_demo_data.seed_company_data")
    def test_create_demo_limit_exceeded(self, mock_seed, client, reseller, db_session):
        _auth_as_reseller(client, reseller)

        # Create 5 demo accounts to hit the limit
        for i in range(5):
            resp = client.post("/api/v1/reseller/clients/demo", json={
                "company_name": f"Demo Limit {i}",
            })
            assert resp.status_code == 201, f"Failed on demo {i}: {resp.json()}"

        # 6th should be rejected
        resp = client.post("/api/v1/reseller/clients/demo", json={
            "company_name": "Demo Over Limit",
        })
        assert resp.status_code == 429

    def test_create_demo_invalid_name(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/clients/demo", json={
            "company_name": "X",  # too short (min_length=2)
        })
        assert resp.status_code == 422


class TestCreateClientAccount:
    """Tests for POST /api/v1/reseller/clients/account."""

    def test_create_account_success(self, client, reseller, db_session):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/clients/account", json={
            "company_name": "Acme Integration Corp",
            "admin_email": "admin@acme-integration.com",
        })
        assert resp.status_code == 201, resp.json()
        data = resp.json()["data"]
        assert data["id"]
        assert data["company_name"] == "Acme Integration Corp"
        assert data["is_demo"] is False
        assert data["source"] == "manual"

    def test_create_account_duplicate_name(self, client, reseller, db_session):
        _auth_as_reseller(client, reseller)
        # First creation
        resp = client.post("/api/v1/reseller/clients/account", json={
            "company_name": "Dup Company",
            "admin_email": "admin@dup-test.com",
        })
        assert resp.status_code == 201

        # Same company name again
        resp = client.post("/api/v1/reseller/clients/account", json={
            "company_name": "Dup Company",
            "admin_email": "admin@dup-test2.com",
        })
        assert resp.status_code == 409

    def test_create_account_invalid_email(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/clients/account", json={
            "company_name": "Valid Name",
            "admin_email": "not-an-email",
        })
        assert resp.status_code == 422


class TestListClients:
    """Tests for GET /api/v1/reseller/clients."""

    def test_empty_list(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/clients")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    @patch("scripts.seed_demo_data.seed_company_data")
    def test_list_with_items(self, mock_seed, client, reseller, db_session):
        _auth_as_reseller(client, reseller)

        # Create a client account first
        client.post("/api/v1/reseller/clients/account", json={
            "company_name": "List Test Corp",
            "admin_email": "admin@listtest.com",
        })

        resp = client.get("/api/v1/reseller/clients")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert item["company_name"]
        assert item["source"]
        assert "plan" in item
        assert "company_status" in item


class TestAdminClientList:
    """Tests for GET /api/v1/admin/resellers/{reseller_id}/clients."""

    def test_admin_list_clients(self, client, auth_as, super_admin_user, reseller, db_session):
        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/admin/resellers/{reseller.id}/clients")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_admin_list_requires_super_admin(self, client, auth_as, admin_user, reseller):
        auth_as(admin_user)
        resp = client.get(f"/api/v1/admin/resellers/{reseller.id}/clients")
        assert resp.status_code == 403


class TestDashboardClientCount:
    """Tests for GET /api/v1/reseller/dashboard — client_count field."""

    def test_dashboard_zero_clients(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["client_count"] == 0

    @patch("scripts.seed_demo_data.seed_company_data")
    def test_dashboard_with_clients(self, mock_seed, client, reseller, db_session):
        _auth_as_reseller(client, reseller)

        # Create a client
        client.post("/api/v1/reseller/clients/account", json={
            "company_name": "Dashboard Count Corp",
            "admin_email": "admin@dashcount.com",
        })

        resp = client.get("/api/v1/reseller/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["client_count"] >= 1
