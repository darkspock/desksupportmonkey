"""Integration tests for /api/v1/companies endpoints (SUPER_ADMIN)."""

import pytest
from unittest.mock import patch, MagicMock

from core.stripe_client import StripeUnavailableError


class TestCreateCompany:
    @patch("core.email.get_email_service")
    def test_create_company_success(self, mock_email, client, auth_as, super_admin_user):
        mock_email.return_value = MagicMock()
        auth_as(super_admin_user)

        resp = client.post("/api/v1/companies", json={
            "name": "Acme Corp",
            "email_domains": ["acme.com"],
            "admin_email": "admin@acme.com",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Acme Corp"
        assert data["status"] == "active"
        assert "acme.com" in data["email_domains"]

    @patch("core.email.get_email_service")
    def test_create_company_stripe_saves_customer_id(self, mock_email, client, auth_as, super_admin_user, db_session):
        mock_email.return_value = MagicMock()
        auth_as(super_admin_user)

        # Override the stripe mock to return a known customer ID
        from adapters.http.api.companies.dependencies import get_stripe_client
        mock_stripe = MagicMock()
        mock_stripe.create_customer.return_value = "cus_saved_test"
        client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        resp = client.post("/api/v1/companies", json={
            "name": "Stripe Test Corp",
            "email_domains": ["stripecorp.io"],
        })

        assert resp.status_code == 201
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        repo = CompanyRepository(db_session)
        company = repo.find_by_stripe_customer_id("cus_saved_test")
        assert company is not None
        assert company.name == "Stripe Test Corp"

    @patch("core.email.get_email_service")
    def test_create_company_stripe_unavailable_returns_503(self, mock_email, client, auth_as, super_admin_user):
        mock_email.return_value = MagicMock()
        auth_as(super_admin_user)

        # Override the stripe mock to raise StripeUnavailableError
        from adapters.http.api.companies.dependencies import get_stripe_client
        mock_stripe = MagicMock()
        mock_stripe.create_customer.side_effect = StripeUnavailableError("down")
        client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        resp = client.post("/api/v1/companies", json={
            "name": "Fail Corp",
            "email_domains": ["failcorp.io"],
        })

        assert resp.status_code == 503
        assert resp.json()["error"]["message"] == "stripe_unavailable"

    @patch("core.email.get_email_service")
    def test_create_company_duplicate_name(self, mock_email, client, auth_as, super_admin_user, company):
        mock_email.return_value = MagicMock()
        auth_as(super_admin_user)

        resp = client.post("/api/v1/companies", json={
            "name": company.name,
            "email_domains": ["other.com"],
            "admin_email": "admin@other.com",
        })

        assert resp.status_code == 409

    @patch("core.email.get_email_service")
    def test_create_company_duplicate_domain(self, mock_email, client, auth_as, super_admin_user, company):
        mock_email.return_value = MagicMock()
        auth_as(super_admin_user)

        resp = client.post("/api/v1/companies", json={
            "name": "Other Corp",
            "email_domains": ["testco.com"],  # already taken by company fixture
            "admin_email": "admin@testco.com",
        })

        assert resp.status_code == 409


class TestListCompanies:
    def test_list_companies(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) >= 1
        assert body["meta"]["total"] >= 1

    def test_list_companies_pagination(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies?page=1&page_size=1")

        assert resp.status_code == 200
        assert resp.json()["meta"]["page"] == 1
        assert resp.json()["meta"]["page_size"] == 1

    def test_list_companies_returns_enriched_fields(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies")

        assert resp.status_code == 200
        item = next(d for d in resp.json()["data"] if d["id"] == company.id)
        assert "user_count" in item
        assert "asset_count" in item
        assert "plan" in item
        assert "billing_status" in item
        assert "trial_days_remaining" in item

    def test_list_companies_filter_in_trial_returns_only_trial_companies(
        self, client, auth_as, super_admin_user, company, db_session
    ):
        from datetime import datetime, timedelta, timezone
        from src.company_bc.company.infrastructure.repository import CompanyRepository

        # give the company an active trial
        company.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=5)
        CompanyRepository(db_session).save(company)
        db_session.flush()

        auth_as(super_admin_user)
        resp = client.get("/api/v1/companies?in_trial=true")

        assert resp.status_code == 200
        ids = [d["id"] for d in resp.json()["data"]]
        assert company.id in ids

    def test_list_companies_filter_plan_returns_only_matching(
        self, client, auth_as, super_admin_user, company
    ):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies?plan=free")

        assert resp.status_code == 200
        # The default company fixture creates a free-plan company
        ids = [d["id"] for d in resp.json()["data"]]
        assert company.id in ids

    def test_list_companies_filter_plan_premium_excludes_free(
        self, client, auth_as, super_admin_user, company
    ):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies?plan=premium")

        assert resp.status_code == 200
        ids = [d["id"] for d in resp.json()["data"]]
        # Default company is free-plan, should not appear in premium filter
        assert company.id not in ids


class TestGetCompanyBillingEnrichment:
    def test_billing_response_includes_trial_fields(
        self, client, auth_as, super_admin_user, company, db_session
    ):
        from datetime import datetime, timedelta, timezone
        from src.company_bc.company.infrastructure.repository import CompanyRepository

        trial_end = datetime.now(timezone.utc) + timedelta(days=8)
        company.trial_ends_at = trial_end
        CompanyRepository(db_session).save(company)
        db_session.flush()

        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/companies/{company.id}/billing")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "trial_days_remaining" in data
        assert "trial_ends_at" in data
        assert data["trial_days_remaining"] is not None
        assert data["trial_days_remaining"] >= 7

    def test_billing_response_no_trial_has_null_trial_fields(
        self, client, auth_as, super_admin_user, company, db_session
    ):
        from src.company_bc.company.infrastructure.repository import CompanyRepository

        company.trial_ends_at = None
        CompanyRepository(db_session).save(company)
        db_session.flush()

        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/companies/{company.id}/billing")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["trial_days_remaining"] is None
        assert data["trial_ends_at"] is None


class TestGetCompany:
    def test_get_company(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get(f"/api/v1/companies/{company.id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == company.id
        assert data["name"] == company.name
        assert "user_count" in data
        assert "department_count" in data

    def test_get_company_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies/nonexistent")

        assert resp.status_code == 404


class TestUpdateCompany:
    def test_update_company(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.put(f"/api/v1/companies/{company.id}", json={
            "name": "Updated Name",
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Name"

    def test_update_company_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.put("/api/v1/companies/nonexistent", json={"name": "X"})

        assert resp.status_code == 404


class TestUpdateCompanyStatus:
    def test_suspend_company(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.patch(f"/api/v1/companies/{company.id}/status", json={
            "status": "suspended",
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "suspended"

    def test_invalid_status_transition(self, client, auth_as, super_admin_user, company, db_session):
        """Deactivate the company, then try to suspend it (invalid)."""
        auth_as(super_admin_user)
        client.patch(f"/api/v1/companies/{company.id}/status", json={"status": "deactivated"})

        resp = client.patch(f"/api/v1/companies/{company.id}/status", json={
            "status": "suspended",
        })

        assert resp.status_code == 409

    def test_status_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.patch("/api/v1/companies/nonexistent/status", json={"status": "suspended"})

        assert resp.status_code == 404


class TestGetCompanyInvoices:
    def test_invoices_returns_list(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)

        resp = client.get(f"/api/v1/companies/{company.id}/invoices")

        assert resp.status_code == 200
        assert "data" in resp.json()
        assert isinstance(resp.json()["data"], list)

    def test_invoices_not_found(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/companies/nonexistent/invoices")

        assert resp.status_code == 404


class TestFounderDashboard:
    def test_dashboard_returns_all_sections(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/super-admin/dashboard")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "revenue" in data
        assert "trials" in data
        assert "health" in data
        assert "growth" in data
        assert "next_milestone" in data
        assert "upcoming_renewals_7d" in data
        assert "as_of" in data

    def test_dashboard_revenue_structure(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/super-admin/dashboard")

        revenue = resp.json()["data"]["revenue"]
        assert "mrr_cents" in revenue
        assert "mrr_formatted" in revenue
        assert "by_plan" in revenue

    def test_dashboard_403_for_non_super_admin(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/super-admin/dashboard")

        assert resp.status_code == 403
