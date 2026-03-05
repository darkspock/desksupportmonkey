"""Integration tests for invite/quick-create flows in membership_only auth mode."""

import pytest

from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.domain.enums import AuthMode
from src.company_bc.company.infrastructure.repository import CompanyRepository


@pytest.fixture()
def membership_only_company(db_session, company):
    """Set the test company to membership_only auth mode."""
    company.set_auth_mode(AuthMode.MEMBERSHIP_ONLY)
    CompanyRepository(db_session).save(company)
    db_session.flush()
    return company


@pytest.fixture()
def admin_membership(db_session, admin_user, company):
    """Create admin CompanyUser membership."""
    cu = CompanyUser.create(
        user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
    )
    CompanyUserRepository(db_session).save(cu)
    db_session.flush()
    return cu


class TestInviteInMembershipOnlyMode:
    def test_invite_public_domain_succeeds_in_membership_only(
        self, client, auth_as, admin_user, membership_only_company, admin_membership,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/users/invite",
            json={"email": "contractor@gmail.com"},
        )

        # Should succeed (201) — domain validation skipped
        assert resp.status_code == 201

    def test_invite_public_domain_fails_in_domain_mode(
        self, client, auth_as, admin_user, company, admin_membership,
    ):
        # Company is in default domain mode
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/users/invite",
            json={"email": "contractor@gmail.com"},
        )

        # Should fail (403) — gmail.com not in company's email domains
        assert resp.status_code == 403

    def test_quick_create_public_domain_succeeds_in_membership_only(
        self, client, auth_as, admin_user, membership_only_company, admin_membership,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/users/quick-create",
            json={"email": "external@outlook.com", "name": "External User"},
        )

        # Should succeed (201) — domain validation skipped
        assert resp.status_code == 201
        assert resp.json()["data"]["email"] == "external@outlook.com"

    def test_quick_create_public_domain_fails_in_domain_mode(
        self, client, auth_as, admin_user, company, admin_membership,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/users/quick-create",
            json={"email": "external@outlook.com", "name": "External User"},
        )

        # Should fail (403)
        assert resp.status_code == 403
