"""Integration tests for reseller payout endpoints (F5)."""
import pytest

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.reseller.dependencies import get_current_reseller, require_active_reseller
from src.reseller_bc.client.domain.entities import ResellerClient
from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.enums import CommissionStatus
from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
from src.reseller_bc.payout.domain.entities import ResellerPayout
from src.reseller_bc.payout.infrastructure.repository import ResellerPayoutRepository
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def reseller(db_session):
    r = Reseller.create(
        email="payout@reseller.com",
        name="Payout Reseller",
        commission_pct=20,
        min_payout_cents=5000,
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def suspended_reseller(db_session):
    r = Reseller.create(
        email="suspended-payout@reseller.com",
        name="Suspended Payout Reseller",
        commission_pct=15,
        min_payout_cents=3000,
    )
    r.suspend()
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def reseller_client(db_session, reseller, company):
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
def confirmed_commission(db_session, reseller, reseller_client, company):
    c = ResellerCommission.create(
        reseller_id=reseller.id,
        reseller_client_id=reseller_client.id,
        company_id=company.id,
        payment_amount_cents=50000,
        commission_pct=20,
        stripe_invoice_id="inv_payout_001",
    )
    c.confirm()
    ResellerCommissionRepository(db_session).save(c)
    db_session.flush()
    return c


def _auth_as_reseller(client, reseller_entity):
    def _override():
        return reseller_entity
    client.app.dependency_overrides[get_current_reseller] = _override

    def _active_override():
        return _override
    client.app.dependency_overrides[require_active_reseller] = _active_override


class TestResellerPayoutEndpoints:
    def test_request_payout_success(self, client, reseller, confirmed_commission):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/payouts")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "requested"
        assert data["amount_cents"] == 10000  # 50000 * 20%

    def test_request_payout_insufficient_balance(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.post("/api/v1/reseller/payouts")
        assert resp.status_code == 400

    def test_request_payout_already_pending(self, client, reseller, confirmed_commission, db_session):
        _auth_as_reseller(client, reseller)
        # First request
        resp1 = client.post("/api/v1/reseller/payouts")
        assert resp1.status_code == 201
        # Second request should fail
        resp2 = client.post("/api/v1/reseller/payouts")
        assert resp2.status_code == 409

    def test_list_reseller_payouts(self, client, reseller, confirmed_commission, db_session):
        _auth_as_reseller(client, reseller)
        # Create a payout first
        client.post("/api/v1/reseller/payouts")
        resp = client.get("/api/v1/reseller/payouts")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_payouts_empty(self, client, reseller):
        _auth_as_reseller(client, reseller)
        resp = client.get("/api/v1/reseller/payouts")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["items"] == []


class TestAdminPayoutEndpoints:
    def test_admin_list_all_payouts(self, client, super_admin_user, auth_as, reseller, confirmed_commission, db_session):
        # Create a payout as reseller
        _auth_as_reseller(client, reseller)
        client.post("/api/v1/reseller/payouts")

        # Switch to admin
        auth_as(super_admin_user)
        resp = client.get("/api/v1/admin/payouts/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_admin_approve_payout(self, client, super_admin_user, auth_as, reseller, confirmed_commission, db_session):
        _auth_as_reseller(client, reseller)
        create_resp = client.post("/api/v1/reseller/payouts")
        assert create_resp.status_code == 201
        payout_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.patch(f"/api/v1/admin/payouts/{payout_id}", json={
            "action": "approve",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "approved"

    def test_admin_reject_payout(self, client, super_admin_user, auth_as, reseller, confirmed_commission, db_session):
        _auth_as_reseller(client, reseller)
        create_resp = client.post("/api/v1/reseller/payouts")
        payout_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.patch(f"/api/v1/admin/payouts/{payout_id}", json={
            "action": "reject",
            "notes": "Please verify bank details",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "rejected"

    def test_admin_mark_paid(self, client, super_admin_user, auth_as, reseller, confirmed_commission, db_session):
        _auth_as_reseller(client, reseller)
        create_resp = client.post("/api/v1/reseller/payouts")
        payout_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        # Approve first
        client.patch(f"/api/v1/admin/payouts/{payout_id}", json={"action": "approve"})
        # Then mark as paid
        resp = client.patch(f"/api/v1/admin/payouts/{payout_id}", json={
            "action": "mark_paid",
            "payment_reference": "WIRE-2026-001",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "paid"

    def test_admin_payout_not_found(self, client, super_admin_user, auth_as):
        auth_as(super_admin_user)
        resp = client.patch("/api/v1/admin/payouts/nonexistent-id", json={
            "action": "approve",
        })
        assert resp.status_code == 404

    def test_admin_non_super_admin_forbidden(self, client, admin_user, auth_as):
        auth_as(admin_user)
        resp = client.get("/api/v1/admin/payouts/")
        assert resp.status_code == 403
