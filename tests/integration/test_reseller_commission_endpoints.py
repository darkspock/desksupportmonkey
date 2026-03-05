"""Integration tests for reseller commission endpoints (F4)."""
import pytest

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.reseller.dependencies import get_current_reseller
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def reseller(db_session):
    """Create an active reseller for commission tests."""
    r = Reseller.create(
        email="commission@reseller.com",
        name="Commission Reseller",
        commission_pct=20,
        min_payout_cents=5000,
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def suspended_reseller(db_session):
    """Create a suspended reseller for commission tests."""
    r = Reseller.create(
        email="suspended-comm@reseller.com",
        name="Suspended Commission Reseller",
        commission_pct=15,
        min_payout_cents=3000,
    )
    r.suspend()
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def reseller_client(db_session, reseller, company):
    """Create a reseller client linked to test company."""
    rc = ResellerClient.create(
        reseller_id=reseller.id,
        company_id=company.id,
        source=ClientSource.MANUAL,
        is_demo=False,
    )
    ResellerClientRepository(db_session).save(rc)
    db_session.flush()
    return rc


@pytest.fixture()
def commission(db_session, reseller, reseller_client, company):
    """Create a commission record for the reseller client."""
    c = ResellerCommission.create(
        reseller_id=reseller.id,
        reseller_client_id=reseller_client.id,
        company_id=company.id,
        payment_amount_cents=10000,
        commission_pct=20,
        stripe_invoice_id="inv_test_001",
    )
    ResellerCommissionRepository(db_session).save(c)
    db_session.flush()
    return c


def _auth_as_reseller(client, reseller_entity):
    """Override get_current_reseller to return the given reseller."""
    def _override():
        return reseller_entity
    client.app.dependency_overrides[get_current_reseller] = _override


class TestResellerCommissionEndpoints:
    def test_list_commissions_returns_data(self, client, reseller, commission):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/commissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["payment_amount_cents"] == 10000
        assert item["commission_pct"] == 20
        assert item["commission_amount_cents"] == 2000
        assert item["status"] == "pending"

    def test_list_commissions_empty(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/commissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []

    def test_suspended_reseller_can_view_commissions(self, client, db_session, suspended_reseller):
        _auth_as_reseller(client, suspended_reseller)
        resp = client.get("/api/v1/reseller/commissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0


class TestAdminCommissionEndpoints:
    def test_admin_can_view_reseller_commissions(self, client, super_admin_user, auth_as, reseller, commission):
        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/admin/resellers/{reseller.id}/commissions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_non_admin_gets_403(self, client, admin_user, auth_as, reseller, commission):
        auth_as(admin_user)
        resp = client.get(f"/api/v1/admin/resellers/{reseller.id}/commissions")
        assert resp.status_code == 403
