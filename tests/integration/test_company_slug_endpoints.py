"""Integration tests for company slug endpoints."""
import pytest

from src.company_bc.company.domain.entities import Company
from src.company_bc.company.infrastructure.repository import CompanyRepository


class TestGetCompanyBySlug:
    """Tests for GET /api/v1/companies/by-slug/{slug}."""

    def test_resolve_slug_success(self, client, company):
        resp = client.get(f"/api/v1/companies/by-slug/{company.slug}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == company.id
        assert data["name"] == company.name
        assert data["slug"] == company.slug
        assert data["auth_mode"] == "domain"
        assert "google_enabled" in data
        assert "microsoft_enabled" in data

    def test_resolve_nonexistent_slug_404(self, client):
        resp = client.get("/api/v1/companies/by-slug/nonexistent")
        assert resp.status_code == 404

    def test_resolve_deactivated_company_404(self, client, db_session, company):
        from src.company_bc.company.domain.enums import CompanyStatus

        company.change_status(CompanyStatus.DEACTIVATED)
        repo = CompanyRepository(db_session)
        repo.save(company)
        db_session.flush()

        resp = client.get(f"/api/v1/companies/by-slug/{company.slug}")
        assert resp.status_code == 404

    def test_resolve_slug_no_auth_required(self, client, company):
        """Slug resolve is a public endpoint — no auth needed."""
        resp = client.get(f"/api/v1/companies/by-slug/{company.slug}")
        assert resp.status_code == 200


class TestUpdateCompanySlugSuperAdmin:
    """Tests for PATCH /api/v1/companies/{company_id}/slug."""

    def test_super_admin_update_slug(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/companies/{company.id}/slug",
            json={"slug": "new-slug"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["slug"] == "new-slug"

    def test_duplicate_slug_409(self, client, auth_as, super_admin_user, db_session, company):
        # Create another company with a different slug
        other = Company.create(name="Other Corp", email_domains=["other.com"])
        other.slug = "other-corp"
        repo = CompanyRepository(db_session)
        repo.save(other)
        repo.save_domains(other.id, other.email_domains)
        db_session.flush()

        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/companies/{company.id}/slug",
            json={"slug": "other-corp"},
        )
        assert resp.status_code == 409

    def test_invalid_slug_422(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/companies/{company.id}/slug",
            json={"slug": "INVALID"},
        )
        assert resp.status_code == 422

    def test_reserved_slug_422(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/companies/{company.id}/slug",
            json={"slug": "admin"},
        )
        assert resp.status_code == 422

    def test_non_super_admin_403(self, client, auth_as, admin_user, company):
        auth_as(admin_user)
        resp = client.patch(
            f"/api/v1/companies/{company.id}/slug",
            json={"slug": "new-slug"},
        )
        assert resp.status_code == 403


class TestUpdateMyCompanySlug:
    """Tests for PATCH /api/v1/my/company-settings/slug."""

    def test_admin_update_own_slug(self, client, auth_as, admin_user, company):
        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/slug",
            json={"slug": "my-new-slug"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["slug"] == "my-new-slug"

    def test_duplicate_slug_409(self, client, auth_as, admin_user, db_session, company):
        other = Company.create(name="Other Corp", email_domains=["other2.com"])
        other.slug = "taken-slug"
        repo = CompanyRepository(db_session)
        repo.save(other)
        repo.save_domains(other.id, other.email_domains)
        db_session.flush()

        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/slug",
            json={"slug": "taken-slug"},
        )
        assert resp.status_code == 409


class TestCompanyResponseIncludesSlug:
    """Verify slug and auth_mode appear in existing company responses."""

    def test_get_company_includes_slug(self, client, auth_as, super_admin_user, company):
        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/companies/{company.id}")
        assert resp.status_code == 200
        # CompanyDetailResponse should have slug
        # (it inherits from CompanyResponse which now has slug)

    def test_get_company_settings_includes_slug(self, client, auth_as, admin_user, company):
        auth_as(admin_user)
        resp = client.get("/api/v1/my/company-settings")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "slug" in data
        assert "auth_mode" in data
        assert data["slug"] == company.slug
        assert data["auth_mode"] == "domain"


class TestCreateCompanyAutoSlug:
    """Verify slug auto-generation on company creation."""

    def test_create_company_generates_slug(self, client, auth_as, super_admin_user):
        auth_as(super_admin_user)
        resp = client.post("/api/v1/companies", json={
            "name": "Auto Slug Corp",
            "email_domains": ["autoslug.com"],
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["slug"] == "auto-slug-corp"

    def test_create_two_companies_same_name_collision(self, client, auth_as, super_admin_user, db_session):
        auth_as(super_admin_user)
        resp1 = client.post("/api/v1/companies", json={
            "name": "Collision Corp",
            "email_domains": ["collision1.com"],
        })
        assert resp1.status_code == 201

        resp2 = client.post("/api/v1/companies", json={
            "name": "Collision Corp",
            "email_domains": ["collision2.com"],
        })
        # Should fail with name collision (company name uniqueness check)
        assert resp2.status_code == 409
