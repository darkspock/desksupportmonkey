"""Integration tests for company switcher endpoints (GET /my-companies, POST /switch-company)."""

import pytest

from core.jwt import JWTService
from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.infrastructure.repository import CompanyRepository


@pytest.fixture()
def company_b(db_session):
    """Create a second company for multi-company tests."""
    c = Company.create(name="Company B", email_domains=["companyb.com"])
    c.slug = Company.generate_slug(c.name)
    repo = CompanyRepository(db_session)
    repo.save(c)
    repo.save_domains(c.id, c.email_domains)
    db_session.flush()
    return c


@pytest.fixture()
def membership_a(db_session, admin_user, company):
    """Create membership for admin_user in the default test company."""
    cu = CompanyUser.create(
        user_id=admin_user.id, company_id=company.id, role=UserRole.ADMIN,
    )
    CompanyUserRepository(db_session).save(cu)
    db_session.flush()
    return cu


@pytest.fixture()
def membership_b(db_session, admin_user, company_b):
    """Create membership for admin_user in company B."""
    cu = CompanyUser.create(
        user_id=admin_user.id, company_id=company_b.id, role=UserRole.EMPLOYEE,
    )
    CompanyUserRepository(db_session).save(cu)
    db_session.flush()
    return cu


class TestListMyCompanies:
    def test_returns_unauthorized_without_auth(self, client):
        resp = client.get("/api/v1/auth/my-companies")
        assert resp.status_code in (401, 403)

    def test_returns_memberships_for_authenticated_user(
        self, client, auth_as, admin_user, company, company_b, membership_a, membership_b,
    ):
        auth_as(admin_user)
        resp = client.get("/api/v1/auth/my-companies")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

        ids = {d["company_id"] for d in data}
        assert company.id in ids
        assert company_b.id in ids

        # Check response shape
        for item in data:
            assert "company_id" in item
            assert "company_name" in item
            assert "slug" in item
            assert "role" in item
            assert "is_current" in item

    def test_super_admin_returns_empty_list(
        self, client, auth_as, super_admin_user,
    ):
        auth_as(super_admin_user)
        resp = client.get("/api/v1/auth/my-companies")

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_filters_inactive_memberships(
        self, client, auth_as, db_session, admin_user, company, company_b, membership_a,
    ):
        # Create inactive membership in company B
        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company_b.id, role=UserRole.EMPLOYEE,
        )
        cu.deactivate()
        CompanyUserRepository(db_session).save(cu)
        db_session.flush()

        auth_as(admin_user)
        resp = client.get("/api/v1/auth/my-companies")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["company_id"] == company.id

    def test_filters_inactive_companies(
        self, client, auth_as, db_session, admin_user, company, company_b, membership_a, membership_b,
    ):
        # Deactivate company B
        company_b.change_status(CompanyStatus.DEACTIVATED)
        repo = CompanyRepository(db_session)
        repo.save(company_b)
        db_session.flush()

        auth_as(admin_user)
        resp = client.get("/api/v1/auth/my-companies")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["company_id"] == company.id

    def test_is_current_flag(
        self, client, auth_as, admin_user, company, company_b, membership_a, membership_b,
    ):
        auth_as(admin_user)
        resp = client.get("/api/v1/auth/my-companies")

        data = resp.json()["data"]
        current = [d for d in data if d["is_current"]]
        assert len(current) == 1
        assert current[0]["company_id"] == company.id


class TestSwitchCompany:
    def test_success_returns_new_jwt(
        self, client, auth_as, admin_user, company, company_b, membership_a, membership_b,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/auth/switch-company",
            json={"company_id": company_b.id},
        )

        assert resp.status_code == 200
        token = resp.json()["data"]["access_token"]
        assert isinstance(token, str)

        # Decode and verify JWT contents
        decoded = JWTService().decode_token(token)
        assert decoded["sub"] == admin_user.id
        assert decoded["company_id"] == company_b.id
        assert decoded["role"] == "employee"

    def test_404_for_no_membership(
        self, client, auth_as, admin_user, company, membership_a,
    ):
        auth_as(admin_user)
        resp = client.post(
            "/api/v1/auth/switch-company",
            json={"company_id": "nonexistent-company-id"},
        )

        assert resp.status_code == 404

    def test_403_for_inactive_membership(
        self, client, auth_as, db_session, admin_user, company, company_b, membership_a,
    ):
        # Create inactive membership in company B
        cu = CompanyUser.create(
            user_id=admin_user.id, company_id=company_b.id, role=UserRole.EMPLOYEE,
        )
        cu.deactivate()
        CompanyUserRepository(db_session).save(cu)
        db_session.flush()

        auth_as(admin_user)
        resp = client.post(
            "/api/v1/auth/switch-company",
            json={"company_id": company_b.id},
        )

        assert resp.status_code == 403

    def test_full_flow_switch_and_verify(
        self, client, auth_as, db_session, admin_user, company, company_b, membership_a, membership_b,
    ):
        auth_as(admin_user)

        # Verify initial state
        me_resp = client.get("/api/v1/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["company_id"] == company.id
        assert me_resp.json()["data"]["role"] == "admin"

        # Switch to company B
        switch_resp = client.post(
            "/api/v1/auth/switch-company",
            json={"company_id": company_b.id},
        )
        assert switch_resp.status_code == 200

        # Re-auth as the (now updated) user to verify state changed
        from src.auth_bc.user.infrastructure.repository import UserRepository
        updated_user = UserRepository(db_session).find_by_id(admin_user.id)
        auth_as(updated_user)

        me_resp2 = client.get("/api/v1/auth/me")
        assert me_resp2.status_code == 200
        assert me_resp2.json()["data"]["company_id"] == company_b.id
        assert me_resp2.json()["data"]["role"] == "employee"

    def test_session_invalidation_old_jwt_rejected(
        self, client, db_session, admin_user, company, company_b, membership_a, membership_b,
    ):
        """After switching, a JWT with the old company_id should be rejected."""
        # Create a real JWT for the user in company A
        jwt_service = JWTService()
        old_token = jwt_service.create_token(
            user_id=admin_user.id,
            company_id=company.id,
            role=admin_user.role.value,
        )

        # Clear any dependency override so real JWT validation runs
        from adapters.http.api.auth.dependencies import get_current_user
        client.app.dependency_overrides.pop(get_current_user, None)

        # Verify old token works before switch
        resp_before = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert resp_before.status_code == 200

        # Now switch company via the service (bypass HTTP to simulate the switch)
        from src.auth_bc.user.application.commands.switch_company import (
            SwitchCompanyRequest, SwitchCompanyService,
        )
        from src.auth_bc.user.infrastructure.repository import UserRepository
        from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository as CURepo

        service = SwitchCompanyService(
            user_repo=UserRepository(db_session),
            company_user_repo=CURepo(db_session),
            jwt_service=jwt_service,
        )
        service.handle(SwitchCompanyRequest(
            user_id=admin_user.id,
            target_company_id=company_b.id,
        ))
        db_session.flush()

        # Old JWT should now be rejected (company_id mismatch)
        resp_after = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert resp_after.status_code == 401
