"""Integration tests for the audit middleware.

The audit middleware creates its own DB session (separate transaction).
For integration tests, we monkeypatch it to use the test session so that
test data is visible and cleaned up by the rollback fixture.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select, func

from src.audit_bc.audit.infrastructure.models import AuditEntryModel
from src.audit_bc.audit.domain.entities import AuditEntry


@pytest.fixture()
def _patch_audit_session(db_session):
    """Make the audit middleware use the test db_session instead of SessionLocal.

    We patch SessionLocal in the audit middleware module so that audit writes
    go into the test transaction (and are rolled back after the test).
    """
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=db_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    # SessionLocal() is called in _record_audit — return a context-manager-like
    # object that actually gives back our real test session.
    def fake_session_local():
        return _FakeSession(db_session)

    with patch(
        "adapters.http.middleware.audit.SessionLocal", fake_session_local
    ):
        yield


class _FakeSession:
    """Wraps the test session so commit/rollback/close are no-ops."""

    def __init__(self, real_session):
        self._s = real_session

    def __getattr__(self, name):
        return getattr(self._s, name)

    def commit(self):
        self._s.flush()

    def rollback(self):
        pass

    def close(self):
        pass


def _count_audit_entries(db_session) -> int:
    return db_session.execute(
        select(func.count()).select_from(AuditEntryModel)
    ).scalar_one()


def _get_last_audit_entry(db_session) -> AuditEntryModel:
    return db_session.execute(
        select(AuditEntryModel).order_by(AuditEntryModel.created_at.desc())
    ).scalar_one()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_audit_session")
class TestAuditMiddlewareCapture:

    def test_post_request_creates_audit_entry(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)
        before = _count_audit_entries(db_session)

        client.post(
            "/api/v1/assets/locations",
            json={"name": "Test Location"},
        )

        after = _count_audit_entries(db_session)
        assert after > before

    def test_get_request_does_not_create_audit_entry(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)
        before = _count_audit_entries(db_session)

        client.get("/api/v1/assets/locations")

        after = _count_audit_entries(db_session)
        assert after == before

    def test_audit_entry_contains_correct_actor(
        self, client, db_session, admin_user, auth_as
    ):
        from core.jwt import JWTService

        auth_as(admin_user)
        token = JWTService().create_token(
            user_id=admin_user.id,
            company_id=str(admin_user.company_id),
            role=admin_user.role.value,
        )

        client.post(
            "/api/v1/assets/locations",
            json={"name": "Actor Test Location"},
            headers={"Authorization": f"Bearer {token}"},
        )

        entry = _get_last_audit_entry(db_session)
        assert entry.actor_id == admin_user.id
        assert entry.company_id == admin_user.company_id

    def test_audit_entry_contains_ip_and_user_agent(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)

        client.post(
            "/api/v1/assets/locations",
            json={"name": "IP Test Location"},
            headers={"User-Agent": "TestAgent/1.0"},
        )

        entry = _get_last_audit_entry(db_session)
        # TestClient uses testclient as host
        assert entry.ip_address is not None
        assert entry.user_agent == "TestAgent/1.0"

    def test_audit_entry_hash_is_valid(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)

        client.post(
            "/api/v1/assets/locations",
            json={"name": "Hash Test Location"},
        )

        entry = _get_last_audit_entry(db_session)
        recomputed = AuditEntry.compute_hash(
            company_id=entry.company_id,
            actor_id=entry.actor_id,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            created_at=entry.created_at,
        )
        assert entry.hash == recomputed

    def test_health_endpoint_not_audited(
        self, client, db_session
    ):
        before = _count_audit_entries(db_session)
        client.get("/api/v1/health")
        after = _count_audit_entries(db_session)
        assert after == before

    def test_delete_request_creates_audit_entry(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)

        # First create a location to delete
        resp = client.post(
            "/api/v1/assets/locations",
            json={"name": "To Delete Location"},
        )
        if resp.status_code == 201:
            loc_id = resp.json()["data"]["id"]
            before = _count_audit_entries(db_session)
            client.delete(f"/api/v1/assets/locations/{loc_id}")
            after = _count_audit_entries(db_session)
            assert after > before

    def test_failed_request_still_audited(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)
        before = _count_audit_entries(db_session)

        # POST to a valid endpoint with invalid data to trigger 422
        client.post("/api/v1/assets/locations", json={})

        after = _count_audit_entries(db_session)
        assert after > before

        entry = _get_last_audit_entry(db_session)
        assert entry.response_status == 422

    def test_audit_entry_action_derived_from_path(
        self, client, db_session, admin_user, auth_as
    ):
        auth_as(admin_user)

        client.post(
            "/api/v1/assets/locations",
            json={"name": "Action Test Location"},
        )

        entry = _get_last_audit_entry(db_session)
        assert entry.http_method == "POST"
        assert entry.http_path == "/api/v1/assets/locations"
        # resource_type derived from path
        assert entry.resource_type in ("asset", "assets")
