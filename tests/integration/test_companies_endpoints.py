"""Integration tests for /api/v1/companies endpoints (SUPER_ADMIN)."""

import pytest
from unittest.mock import patch, MagicMock


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
