"""Integration tests for PATCH /my/company-settings/auth-mode endpoint."""

import pytest

from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.domain.enums import AuthMode
from src.company_bc.company.infrastructure.repository import CompanyRepository


@pytest.fixture()
def admin_membership(db_session, admin_user, company):
    """Create admin CompanyUser membership for lockout prevention."""
    cu = CompanyUser.create(
        user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
    )
    CompanyUserRepository(db_session).save(cu)
    db_session.flush()
    return cu


class TestUpdateAuthMode:
    def test_returns_unauthorized_without_auth(self, client):
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "membership_only"},
        )
        assert resp.status_code in (401, 403)

    def test_returns_403_for_non_admin(self, client, auth_as, employee_user):
        auth_as(employee_user)
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "membership_only"},
        )
        assert resp.status_code == 403

    def test_switch_domain_to_membership_only_success(
        self, client, auth_as, admin_user, company, admin_membership,
    ):
        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "membership_only"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["auth_mode"] == "membership_only"

    def test_switch_membership_only_to_domain_success(
        self, client, auth_as, db_session, admin_user, company, admin_membership,
    ):
        # First switch to membership_only
        company.set_auth_mode(AuthMode.MEMBERSHIP_ONLY)
        CompanyRepository(db_session).save(company)
        db_session.flush()

        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "domain"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["auth_mode"] == "domain"

    def test_returns_409_when_no_admin_memberships(
        self, client, auth_as, admin_user, company,
    ):
        # No admin_membership fixture — zero admin CompanyUser records
        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "membership_only"},
        )

        assert resp.status_code == 409

    def test_round_trip_toggle_both_directions(
        self, client, auth_as, db_session, admin_user, company, admin_membership,
    ):
        auth_as(admin_user)

        # Domain -> membership_only
        resp1 = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "membership_only"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["data"]["auth_mode"] == "membership_only"

        # Verify via GET
        get_resp = client.get("/api/v1/my/company-settings")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["auth_mode"] == "membership_only"

        # Membership_only -> domain
        resp2 = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "domain"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["auth_mode"] == "domain"

        # Verify via GET
        get_resp2 = client.get("/api/v1/my/company-settings")
        assert get_resp2.status_code == 200
        assert get_resp2.json()["data"]["auth_mode"] == "domain"

    def test_returns_422_for_invalid_auth_mode(
        self, client, auth_as, admin_user, company,
    ):
        auth_as(admin_user)
        resp = client.patch(
            "/api/v1/my/company-settings/auth-mode",
            json={"auth_mode": "invalid_mode"},
        )

        assert resp.status_code == 422
