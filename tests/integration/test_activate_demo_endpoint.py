"""Integration tests for POST /api/v1/my/activate-demo endpoint."""

import pytest

from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.infrastructure.repository import CompanyRepository


@pytest.fixture()
def demo_company(db_session):
    """Create a demo company in the test DB."""
    from src.company_bc.company.domain.entities import Company
    from src.asset_bc.asset.domain.entities import AssetLocation
    from src.asset_bc.asset.domain.enums import SystemLocation
    from src.asset_bc.asset.infrastructure.repository import AssetRepository

    c = Company.create(
        name="Demo Corp (Demo)", email_domains=["demo.local"], is_demo=True,
    )
    c.slug = Company.generate_slug(c.name)
    repo = CompanyRepository(db_session)
    repo.save(c)
    repo.save_domains(c.id, c.email_domains)

    asset_repo = AssetRepository(db_session)
    for key, name in {
        SystemLocation.IN_TRANSIT.value: "In Transit",
        SystemLocation.MAIN_WAREHOUSE.value: "Main Warehouse",
    }.items():
        loc = AssetLocation.create(
            company_id=c.id, name=name, is_system=True, system_key=key,
        )
        asset_repo.save_location(loc)

    db_session.flush()
    return c


@pytest.fixture()
def demo_admin(db_session, demo_company):
    """Create an admin user belonging to the demo company."""
    from datetime import datetime, timezone
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    user = User.create(
        email="admin@demo.local",
        role=UserRole.ADMIN,
        company_id=demo_company.id,
        name="Demo Admin",
    )
    user.email_verified_at = datetime.now(timezone.utc)
    UserRepository(db_session).save(user)
    db_session.flush()
    return user


@pytest.fixture()
def demo_client(db_session, client):
    """TestClient with my/dependencies.get_stripe_client overridden."""
    from unittest.mock import MagicMock
    from adapters.http.api.my.dependencies import get_stripe_client

    mock_stripe = MagicMock()
    mock_stripe.create_customer.return_value = "cus_activated_test"
    client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe
    yield client


class TestActivateDemoEndpoint:
    def test_returns_401_without_auth(self, demo_client):
        resp = demo_client.post(
            "/api/v1/my/activate-demo",
            json={
                "company_name": "Real Corp",
                "email_domains": ["realcorp.com"],
            },
        )
        assert resp.status_code in (401, 403)

    def test_returns_403_for_non_admin(
        self, demo_client, auth_as, db_session, demo_company,
    ):
        from src.auth_bc.user.domain.entities import User
        from src.auth_bc.user.domain.enums import UserRole
        from src.auth_bc.user.infrastructure.repository import UserRepository

        employee = User.create(
            email="emp@demo.local",
            role=UserRole.EMPLOYEE,
            company_id=demo_company.id,
        )
        UserRepository(db_session).save(employee)
        db_session.flush()

        auth_as(employee)
        resp = demo_client.post(
            "/api/v1/my/activate-demo",
            json={
                "company_name": "Real Corp",
                "email_domains": ["realcorp.com"],
            },
        )
        assert resp.status_code == 403

    def test_happy_path_activates_demo(
        self, demo_client, auth_as, db_session, demo_admin, demo_company,
    ):
        auth_as(demo_admin)
        resp = demo_client.post(
            "/api/v1/my/activate-demo",
            json={
                "company_name": "Real Corp",
                "email_domains": ["realcorp.com"],
                "keep_demo_data": True,
            },
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["message"] == "Demo account activated successfully"

        # Verify company was updated in DB
        company = CompanyRepository(db_session).find_by_id(demo_company.id)
        assert company.plan == PlanTier.FREE
        assert company.name == "Real Corp"
        assert company.stripe_customer_id == "cus_activated_test"

    def test_returns_409_for_non_demo_company(
        self, demo_client, auth_as, db_session, company, admin_user,
    ):
        """Use the standard conftest company (FREE plan, not demo)."""
        auth_as(admin_user)
        resp = demo_client.post(
            "/api/v1/my/activate-demo",
            json={
                "company_name": "New Name",
                "email_domains": ["newdomain.com"],
            },
        )
        assert resp.status_code == 409

    def test_returns_422_for_blocked_domain(
        self, demo_client, auth_as, demo_admin,
    ):
        auth_as(demo_admin)
        resp = demo_client.post(
            "/api/v1/my/activate-demo",
            json={
                "company_name": "Real Corp",
                "email_domains": ["gmail.com"],
            },
        )
        assert resp.status_code == 422

    def test_get_me_returns_demo_fields(
        self, demo_client, auth_as, demo_admin, demo_company,
    ):
        auth_as(demo_admin)
        resp = demo_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["company_plan"] == "demo"
        assert data["demo_days_remaining"] is not None
        assert data["demo_days_remaining"] >= 13

    def test_get_me_returns_null_demo_fields_for_free(
        self, demo_client, auth_as, admin_user,
    ):
        auth_as(admin_user)
        resp = demo_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["company_plan"] == "free"
        assert data["demo_days_remaining"] is None
