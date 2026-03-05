"""Integration tests for registration with referral attribution (F3)."""
import pytest
from unittest.mock import patch, MagicMock

from src.reseller_bc.client.domain.enums import ClientSource
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository


@pytest.fixture()
def reseller(db_session):
    """Create an active reseller for referral tests."""
    r = Reseller.create(
        email="referral@reseller.com",
        name="Referral Reseller",
        commission_pct=20,
        min_payout_cents=5000,
    )
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


@pytest.fixture()
def suspended_reseller(db_session):
    """Create a suspended reseller for referral tests."""
    r = Reseller.create(
        email="suspended-ref@reseller.com",
        name="Suspended Referral Reseller",
        commission_pct=15,
        min_payout_cents=3000,
    )
    r.suspend()
    ResellerRepository(db_session).save(r)
    db_session.flush()
    return r


class TestRegistrationReferral:
    """Tests for POST /api/v1/register with referral_code parameter."""

    @patch("core.email.get_email_service")
    def test_register_with_valid_referral(self, mock_email, client, reseller, db_session):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "Referred Corp",
            "admin_email": "admin@referredcorp.com",
            "email_domains": ["referredcorp.com"],
            "referral_code": reseller.referral_code,
        })

        assert resp.status_code == 201
        # Verify ResellerClient created with source=referral
        clients = ResellerClientRepository(db_session).find_by_reseller_id(reseller.id)
        assert len(clients) == 1
        assert clients[0].source == ClientSource.REFERRAL
        assert clients[0].is_demo is False

    @patch("core.email.get_email_service")
    def test_register_with_invalid_referral_code(self, mock_email, client, db_session):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "No Ref Corp",
            "admin_email": "admin@norefcorp.com",
            "email_domains": ["norefcorp.com"],
            "referral_code": "nonexistent_code",
        })

        # Company still created successfully
        assert resp.status_code == 201
        # No ResellerClient created
        from src.reseller_bc.client.infrastructure.models import ResellerClientModel
        count = db_session.query(ResellerClientModel).count()
        assert count == 0

    @patch("core.email.get_email_service")
    def test_register_without_referral_code(self, mock_email, client, db_session):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "Normal Corp",
            "admin_email": "admin@normalcorp.com",
            "email_domains": ["normalcorp.com"],
        })

        assert resp.status_code == 201
        # No ResellerClient created
        from src.reseller_bc.client.infrastructure.models import ResellerClientModel
        count = db_session.query(ResellerClientModel).count()
        assert count == 0

    @patch("core.email.get_email_service")
    def test_register_with_suspended_reseller_code(self, mock_email, client, suspended_reseller, db_session):
        mock_email.return_value = MagicMock()

        resp = client.post("/api/v1/register", json={
            "name": "Suspended Ref Corp",
            "admin_email": "admin@suspendedrefcorp.com",
            "email_domains": ["suspendedrefcorp.com"],
            "referral_code": suspended_reseller.referral_code,
        })

        # Company still created successfully
        assert resp.status_code == 201
        # No ResellerClient created (suspended resellers don't get attribution)
        clients = ResellerClientRepository(db_session).find_by_reseller_id(suspended_reseller.id)
        assert len(clients) == 0
