"""
Root conftest for integration tests.

Provides real PostgreSQL database fixtures, FastAPI TestClient, and auth helpers.
Requires Docker PostgreSQL running on localhost:5444.
"""

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from core.base import Base

TEST_DB_NAME = "dsm_test"
TEST_DB_URL = f"postgresql://postgres:postgres@localhost:5444/{TEST_DB_NAME}"


# ---------------------------------------------------------------------------
# Database lifecycle
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def create_test_database():
    """Create the test database if it doesn't exist (session-scoped)."""
    conn = psycopg2.connect(
        dbname="postgres", user="postgres", password="postgres", host="localhost", port=5444,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
    if not cur.fetchone():
        cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    cur.close()
    conn.close()


@pytest.fixture(scope="session")
def test_engine(create_test_database):
    """Create a SQLAlchemy engine bound to the test database."""
    engine = create_engine(TEST_DB_URL, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tables(test_engine):
    """Create all tables at the start, drop at the end."""
    # Import all ORM models so Base.metadata knows about them
    import src.auth_bc.user.infrastructure.models  # noqa: F401
    import src.auth_bc.magic_link.infrastructure.models  # noqa: F401
    import src.company_bc.company.infrastructure.models  # noqa: F401
    import src.company_bc.department.infrastructure.models  # noqa: F401
    import src.asset_bc.asset.infrastructure.models  # noqa: F401
    import src.request_bc.request.infrastructure.models  # noqa: F401
    import src.notification_bc.notification.infrastructure.models  # noqa: F401
    import src.report_bc.report.infrastructure.models  # noqa: F401
    import src.mcp_bc.server.infrastructure.models  # noqa: F401
    import src.company_bc.employee_role.infrastructure.models  # noqa: F401
    import src.company_bc.equipment_profile.infrastructure.models  # noqa: F401
    import src.company_bc.assignment_config.infrastructure.models  # noqa: F401
    import src.company_bc.classification_config.infrastructure.models  # noqa: F401
    import src.procurement_bc.vendor.infrastructure.models  # noqa: F401
    import src.procurement_bc.purchase_order.infrastructure.models  # noqa: F401
    import src.procurement_bc.budget.infrastructure.models  # noqa: F401
    import src.appointment_bc.appointment.infrastructure.models  # noqa: F401
    import src.shipping_bc.shipment.infrastructure.models  # noqa: F401
    import src.shipping_bc.address.infrastructure.models  # noqa: F401
    import src.maintenance_bc.maintenance_template.infrastructure.models  # noqa: F401
    import src.maintenance_bc.maintenance_record.infrastructure.models  # noqa: F401
    import src.incident_bc.incident.infrastructure.models  # noqa: F401
    import src.risk_bc.risk.infrastructure.models  # noqa: F401
    import src.audit_bc.audit.infrastructure.models  # noqa: F401
    import src.custom_field_bc.definition.infrastructure.models  # noqa: F401
    import src.workflow_bc.template.infrastructure.models  # noqa: F401
    import src.workflow_bc.checklist.infrastructure.models  # noqa: F401
    import src.company_bc.nav_config.infrastructure.models  # noqa: F401
    import src.company_bc.sla_escalation_config.infrastructure.models  # noqa: F401
    import src.sla_bc.sla.infrastructure.models  # noqa: F401
    import src.asset_bc.checkout.infrastructure.models  # noqa: F401
    import src.asset_type_bc.definition.infrastructure.models  # noqa: F401
    import src.vulnerability_bc.vulnerability.infrastructure.models  # noqa: F401
    import src.change_bc.change_request.infrastructure.models  # noqa: F401
    import src.reseller_bc.reseller.infrastructure.models  # noqa: F401
    import src.reseller_bc.client.infrastructure.models  # noqa: F401
    import src.reseller_bc.commission.infrastructure.models  # noqa: F401
    import src.reseller_bc.payout.infrastructure.models  # noqa: F401
    import src.auth_bc.company_user.infrastructure.models  # noqa: F401
    import src.support_bc.ticket.infrastructure.models  # noqa: F401

    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def db_session(test_engine, tables):
    """
    Per-test database session with transaction rollback.

    Uses a connection-level transaction that wraps the entire test.
    Handler commit() calls release savepoints instead of real commits,
    and the outer transaction is rolled back after each test.
    """
    conn = test_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    trans.rollback()
    conn.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(db_session):
    """
    FastAPI TestClient wired to the test database session.

    Overrides:
    - get_db  -> yields the test db_session
    - get_event_bus -> returns a no-op EventBus (no subscribers)
    - get_stripe_client (all routers) -> returns a no-op MagicMock (no real Stripe calls)
    """
    from unittest.mock import MagicMock
    from starlette.testclient import TestClient
    from app import create_app
    from core.database import get_db
    from adapters.http.api.dependencies import get_event_bus
    from adapters.http.api.companies.dependencies import get_stripe_client as get_stripe_client_companies
    from adapters.http.api.registration.dependencies import get_stripe_client as get_stripe_client_registration
    from adapters.http.api.billing.dependencies import get_stripe_client as get_stripe_client_billing
    from adapters.http.api.billing.dependencies import get_billing_service
    from adapters.http.api.super_admin.dependencies import get_stripe_client as get_stripe_client_super_admin
    from src.notification_bc.notification.application.services.event_bus import EventBus

    application = create_app()

    def _override_get_db():
        yield db_session

    mock_stripe = MagicMock()
    mock_stripe.create_customer.return_value = "cus_test_mock"

    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_event_bus] = lambda: EventBus()  # no subscribers
    application.dependency_overrides[get_stripe_client_companies] = lambda: mock_stripe
    application.dependency_overrides[get_stripe_client_registration] = lambda: mock_stripe
    application.dependency_overrides[get_stripe_client_billing] = lambda: mock_stripe
    application.dependency_overrides[get_stripe_client_super_admin] = lambda: mock_stripe

    mock_billing_service = MagicMock()
    mock_billing_service.create_checkout_session.return_value = "https://checkout.stripe.com/test"
    mock_billing_service.create_portal_session.return_value = "https://billing.stripe.com/test"
    application.dependency_overrides[get_billing_service] = lambda: mock_billing_service

    with TestClient(application, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _auth_as(client, user):
    """Override get_current_user to return the given user and set tenant context."""
    from adapters.http.api.auth.dependencies import get_current_user
    from core.tenant import set_tenant

    def _override():
        set_tenant(company_id=user.company_id, user_id=user.id, role=user.role.value)
        return user

    client.app.dependency_overrides[get_current_user] = _override


@pytest.fixture()
def auth_as(client):
    """Fixture that returns a helper to authenticate as a given user."""
    def _do_auth(user):
        _auth_as(client, user)
    return _do_auth


# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------


@pytest.fixture()
def company(db_session):
    """Create a real company in the test DB (with email domains and system locations)."""
    from src.company_bc.company.domain.entities import Company
    from src.company_bc.company.infrastructure.repository import CompanyRepository
    from src.asset_bc.asset.domain.entities import AssetLocation
    from src.asset_bc.asset.domain.enums import SystemLocation
    from src.asset_bc.asset.infrastructure.repository import AssetRepository

    c = Company.create(name="Test Company", email_domains=["testco.com"])
    c.slug = Company.generate_slug(c.name)
    repo = CompanyRepository(db_session)
    repo.save(c)
    repo.save_domains(c.id, c.email_domains)

    # Seed system locations (same as CreateCompanyCommandHandler)
    asset_repo = AssetRepository(db_session)
    system_names = {
        SystemLocation.IN_TRANSIT.value: "In Transit",
        SystemLocation.MAIN_WAREHOUSE.value: "Main Warehouse",
    }
    for key, name in system_names.items():
        loc = AssetLocation.create(
            company_id=c.id, name=name, is_system=True, system_key=key,
        )
        asset_repo.save_location(loc)

    db_session.flush()
    return c


@pytest.fixture()
def super_admin_user(db_session):
    """Create a super admin (no company)."""
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    u = User.create(email="superadmin@platform.com", role=UserRole.SUPER_ADMIN)
    UserRepository(db_session).save(u)
    db_session.flush()
    return u


@pytest.fixture()
def admin_user(db_session, company):
    """Create an admin user belonging to the test company."""
    from datetime import datetime, timezone
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    u = User.create(email="admin@testco.com", role=UserRole.ADMIN, company_id=company.id)
    u.email_verified_at = datetime.now(timezone.utc)
    UserRepository(db_session).save(u)
    db_session.flush()
    return u


@pytest.fixture()
def technician_user(db_session, company):
    """Create a technician user belonging to the test company."""
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    u = User.create(email="tech@testco.com", role=UserRole.TECHNICIAN, company_id=company.id)
    UserRepository(db_session).save(u)
    db_session.flush()
    return u


@pytest.fixture()
def employee_user(db_session, company):
    """Create an employee user belonging to the test company."""
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    u = User.create(email="employee@testco.com", role=UserRole.EMPLOYEE, company_id=company.id)
    UserRepository(db_session).save(u)
    db_session.flush()
    return u


@pytest.fixture()
def make_user(db_session):
    """Factory fixture to create users with custom attributes."""
    from src.auth_bc.user.domain.entities import User
    from src.auth_bc.user.domain.enums import UserRole
    from src.auth_bc.user.infrastructure.repository import UserRepository

    def _make(email, role=UserRole.EMPLOYEE, company_id=None, name=None, department_id=None, employee_role_id=None):
        u = User.create(email=email, role=role, company_id=company_id, name=name, department_id=department_id)
        if employee_role_id:
            u.assign_employee_role(employee_role_id)
        UserRepository(db_session).save(u)
        db_session.flush()
        return u

    return _make
