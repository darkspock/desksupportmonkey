"""Integration tests for /api/v1/companies/{id}/billing endpoints (SUPER_ADMIN)."""

import pytest
from unittest.mock import MagicMock, patch

from adapters.http.api.companies.dependencies import get_stripe_client
from app import app
from core.stripe_client import StripeUnavailableError
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.infrastructure.repository import CompanyRepository


class TestGetCompanyBilling:
    def test_returns_billing_data_for_super_admin(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get(f"/api/v1/companies/{company.id}/billing")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["company_id"] == company.id
        assert data["plan"] == "free"
        assert data["billing_status"] == "active"
        assert data["complimentary"] is False

    def test_returns_404_for_unknown_company(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies/nonexistent/billing")

        assert resp.status_code == 404

    def test_non_super_admin_returns_403(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get(f"/api/v1/companies/{admin_user.company_id}/billing")

        assert resp.status_code == 403


class TestOverrideCompanyBillingPlan:
    def test_overrides_plan_to_enterprise(self, client, auth_as, super_admin_user, company, db_session):
        auth_as(super_admin_user)

        resp = client.patch(
            f"/api/v1/companies/{company.id}/billing/plan",
            json={"new_plan": "enterprise"},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["plan"] == "enterprise"
        assert data["billing_status"] == "active"

        refreshed = CompanyRepository(db_session).find_by_id(company.id)
        assert refreshed is not None
        assert refreshed.plan == PlanTier.ENTERPRISE
        assert refreshed.billing_status == BillingStatus.ACTIVE

    def test_invalid_plan_returns_422(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.patch(
            f"/api/v1/companies/{company.id}/billing/plan",
            json={"new_plan": "not_a_plan"},
        )

        assert resp.status_code == 422

    def test_unknown_company_returns_404(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.patch(
            "/api/v1/companies/nonexistent/billing/plan",
            json={"new_plan": "premium"},
        )

        assert resp.status_code == 404


class TestGrantComplimentaryPlan:
    def test_grants_complimentary_no_stripe_sub(self, client, auth_as, super_admin_user, company, db_session):
        auth_as(super_admin_user)
        mock_stripe = MagicMock()
        app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        try:
            resp = client.post(
                f"/api/v1/companies/{company.id}/billing/complimentary",
                json={"plan": "enterprise"},
            )
        finally:
            app.dependency_overrides.pop(get_stripe_client, None)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["complimentary"] is True
        assert data["plan"] == "enterprise"
        mock_stripe.cancel_subscription.assert_not_called()

    def test_cancels_stripe_subscription_when_present(self, client, auth_as, super_admin_user, company, db_session):
        from src.company_bc.company.infrastructure.repository import CompanyRepository as CR
        repo = CR(db_session)
        company.stripe_subscription_id = "sub_test_123"
        repo.save(company)
        db_session.flush()

        auth_as(super_admin_user)
        mock_stripe = MagicMock()
        app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        try:
            resp = client.post(
                f"/api/v1/companies/{company.id}/billing/complimentary",
                json={"plan": "enterprise"},
            )
        finally:
            app.dependency_overrides.pop(get_stripe_client, None)

        assert resp.status_code == 200
        mock_stripe.cancel_subscription.assert_called_once_with("sub_test_123")

    def test_stripe_failure_returns_503(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)
        mock_stripe = MagicMock()
        mock_stripe.cancel_subscription.side_effect = StripeUnavailableError()
        app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        from src.company_bc.company.infrastructure.repository import CompanyRepository as CR
        # give company a subscription so the cancel path is hit
        with pytest.MonkeyPatch().context() as m:
            m.setattr(company, "stripe_subscription_id", "sub_fail")
            try:
                resp = client.post(
                    f"/api/v1/companies/{company.id}/billing/complimentary",
                    json={"plan": "enterprise"},
                )
            finally:
                app.dependency_overrides.pop(get_stripe_client, None)

        assert resp.status_code == 503

    def test_invalid_plan_returns_422(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.post(
            f"/api/v1/companies/{company.id}/billing/complimentary",
            json={"plan": "invalid"},
        )

        assert resp.status_code == 422


class TestRevokeComplimentaryPlan:
    def test_revokes_complimentary_sets_over_limit(self, client, auth_as, super_admin_user, company, db_session):
        from src.company_bc.company.infrastructure.repository import CompanyRepository as CR
        repo = CR(db_session)
        company.grant_complimentary(PlanTier.ENTERPRISE)
        repo.save(company)
        db_session.flush()

        auth_as(super_admin_user)

        resp = client.delete(f"/api/v1/companies/{company.id}/billing/complimentary")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["complimentary"] is False
        assert data["plan"] == "free"
        assert data["billing_status"] == "over_limit"

    def test_revoke_non_complimentary_returns_422(self, client, auth_as, super_admin_user, company, db_session):
        auth_as(super_admin_user)

        resp = client.delete(f"/api/v1/companies/{company.id}/billing/complimentary")

        assert resp.status_code == 422

    def test_unknown_company_returns_404(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.delete("/api/v1/companies/nonexistent/billing/complimentary")

        assert resp.status_code == 404
