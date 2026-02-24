"""Integration tests for audit UI, export & compliance endpoints."""
import pytest
from unittest.mock import patch, MagicMock

from src.audit_bc.audit.domain.entities import AuditEntry
from src.audit_bc.audit.infrastructure.repository import AuditRepository


@pytest.fixture()
def audit_entry(db_session, company):
    """Create a real audit entry in the test DB."""
    entry = AuditEntry.create(
        company_id=company.id,
        actor_id=None,
        actor_email="admin@testco.com",
        action="asset.created",
        resource_type="asset",
        resource_id="01TESTASSET000000000000AB",
        http_method="POST",
        http_path="/api/v1/assets",
        ip_address="127.0.0.1",
        user_agent="TestAgent",
        request_data={"name": "Laptop"},
        response_status=201,
    )
    repo = AuditRepository(db_session)
    repo.save(entry)
    db_session.flush()
    return entry


@pytest.fixture()
def custom_control(db_session, company):
    """Create a custom compliance control."""
    from src.audit_bc.audit.domain.entities import ComplianceControl

    control = ComplianceControl.create(
        company_id=company.id,
        code="TEST-001",
        name="Test Control",
        framework="TEST",
        description="A test control",
    )
    repo = AuditRepository(db_session)
    repo.save_control(control)
    db_session.flush()
    return control


@pytest.fixture()
def predefined_control(db_session):
    """Create a predefined compliance control."""
    from src.audit_bc.audit.domain.entities import ComplianceControl

    control = ComplianceControl.create(
        company_id=None,
        code="NIS2-TEST",
        name="NIS2 Test Control",
        framework="NIS2",
        is_predefined=True,
    )
    repo = AuditRepository(db_session)
    repo.save_control(control)
    db_session.flush()
    return control


def _make_enterprise(db_session, company):
    """Set company to Enterprise plan."""
    from sqlalchemy import update
    from src.company_bc.company.infrastructure.models import CompanyModel

    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(plan="enterprise", billing_status="active")
    )
    db_session.flush()


def _expire_trial(db_session, company):
    """Expire company trial so plan gate enforces the free plan."""
    from sqlalchemy import update
    from datetime import datetime, timezone, timedelta
    from src.company_bc.company.infrastructure.models import CompanyModel

    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(trial_ends_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    )
    db_session.flush()


# ---------------------------------------------------------------------------
# Audit entry list
# ---------------------------------------------------------------------------


class TestAuditListEndpoint:

    def test_list_audit_entries(
        self, client, db_session, admin_user, auth_as, company, audit_entry
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit")

        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data
        assert data["meta"]["total"] >= 1

    def test_list_returns_402_for_free_plan(
        self, client, db_session, admin_user, auth_as, company
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)
        resp = client.get("/api/v1/audit")
        assert resp.status_code == 402

    def test_list_returns_403_for_employee(
        self, client, db_session, employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(employee_user)
        resp = client.get("/api/v1/audit")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Audit entry detail
# ---------------------------------------------------------------------------


class TestAuditDetailEndpoint:

    def test_get_audit_entry_detail(
        self, client, db_session, admin_user, auth_as, company, audit_entry
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get(f"/api/v1/audit/{audit_entry.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == audit_entry.id
        assert data["action"] == "asset.created"
        assert "tags" in data

    def test_get_nonexistent_entry(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/01NONEXISTENT0000000000000")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Compliance controls
# ---------------------------------------------------------------------------


class TestComplianceControlsEndpoint:

    def test_list_controls(
        self, client, db_session, admin_user, auth_as, company,
        predefined_control, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/controls")

        assert resp.status_code == 200
        data = resp.json()["data"]
        codes = [c["code"] for c in data]
        assert "NIS2-TEST" in codes
        assert "TEST-001" in codes

    def test_create_custom_control(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/controls",
            json={
                "code": "NEW-001",
                "name": "New Control",
                "framework": "CUSTOM",
                "description": "desc",
            },
        )

        assert resp.status_code == 201

    def test_create_duplicate_code_returns_409(
        self, client, db_session, admin_user, auth_as, company, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/controls",
            json={
                "code": "TEST-001",  # already exists
                "name": "Duplicate",
                "framework": "TEST",
            },
        )

        assert resp.status_code == 409

    def test_update_custom_control(
        self, client, db_session, admin_user, auth_as, company, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/audit/controls/{custom_control.id}",
            json={"name": "Updated Name"},
        )

        assert resp.status_code == 200

    def test_update_predefined_returns_409(
        self, client, db_session, admin_user, auth_as,
        company, predefined_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/audit/controls/{predefined_control.id}",
            json={"name": "Modified"},
        )

        assert resp.status_code == 409

    def test_deactivate_custom_control(
        self, client, db_session, admin_user, auth_as, company, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.delete(
            f"/api/v1/audit/controls/{custom_control.id}"
        )

        assert resp.status_code == 200

    def test_deactivate_predefined_returns_409(
        self, client, db_session, admin_user, auth_as,
        company, predefined_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.delete(
            f"/api/v1/audit/controls/{predefined_control.id}"
        )

        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TestAuditTagsEndpoint:

    def test_add_tags_to_entry(
        self, client, db_session, admin_user, auth_as, company,
        audit_entry, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            f"/api/v1/audit/{audit_entry.id}/tags",
            json={"control_ids": [custom_control.id]},
        )

        assert resp.status_code == 201

    def test_remove_tag_from_entry(
        self, client, db_session, admin_user, auth_as, company,
        audit_entry, custom_control
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # First add a tag
        from src.audit_bc.audit.domain.entities import AuditEntryTag
        tag = AuditEntryTag.create(
            audit_entry_id=audit_entry.id,
            control_id=custom_control.id,
            tagged_by=admin_user.id,
        )
        AuditRepository(db_session).save_tag(tag)
        db_session.flush()

        resp = client.delete(
            f"/api/v1/audit/{audit_entry.id}/tags/{tag.id}"
        )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestAuditExportEndpoint:

    @patch("core.tasks.audit.export_audit_log")
    def test_request_export(
        self, mock_task, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_task.delay.return_value = mock_result

        resp = client.post(
            "/api/v1/audit/export",
            json={"format": "csv"},
        )

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "task-123"


# ---------------------------------------------------------------------------
# Super Admin
# ---------------------------------------------------------------------------


class TestSuperAdminAuditEndpoint:

    def test_super_admin_can_list_cross_company(
        self, client, db_session, super_admin_user, auth_as, audit_entry
    ):
        auth_as(super_admin_user)

        resp = client.get("/api/v1/super-admin/audit")

        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data

    def test_non_super_admin_cannot_access(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/super-admin/audit")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GDPR Endpoints
# ---------------------------------------------------------------------------


class TestGdprListEndpoint:

    def test_list_gdpr_requests_empty(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/gdpr")

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["meta"]["total"] == 0

    def test_list_returns_402_for_free_plan(
        self, client, db_session, admin_user, auth_as, company
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)
        resp = client.get("/api/v1/audit/gdpr")
        assert resp.status_code == 402

    def test_list_returns_403_for_employee(
        self, client, db_session, employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(employee_user)
        resp = client.get("/api/v1/audit/gdpr")
        assert resp.status_code == 403


class TestGdprExportEndpoint:

    @patch("core.tasks.gdpr.gdpr_data_export")
    def test_request_export_success(
        self, mock_task, client, db_session, admin_user,
        employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_task.delay.return_value = None

        resp = client.post(
            "/api/v1/audit/gdpr/export",
            json={"target_user_email": employee_user.email},
        )

        assert resp.status_code == 202
        assert "id" in resp.json()
        mock_task.delay.assert_called_once()

    @patch("core.tasks.gdpr.gdpr_data_export")
    def test_request_export_user_not_found(
        self, mock_task, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/gdpr/export",
            json={"target_user_email": "nobody@example.com"},
        )

        assert resp.status_code == 404
        mock_task.delay.assert_not_called()


class TestGdprAnonymizeEndpoint:

    @patch("core.tasks.gdpr.gdpr_anonymize_user")
    def test_request_anonymize_success(
        self, mock_task, client, db_session, admin_user,
        employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_task.delay.return_value = None

        resp = client.post(
            "/api/v1/audit/gdpr/anonymize",
            json={
                "target_user_email": employee_user.email,
                "reason": "GDPR right to be forgotten",
            },
        )

        assert resp.status_code == 202
        assert "id" in resp.json()

    @patch("core.tasks.gdpr.gdpr_anonymize_user")
    def test_anonymize_self_returns_409(
        self, mock_task, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/gdpr/anonymize",
            json={
                "target_user_email": admin_user.email,
                "reason": "test",
            },
        )

        assert resp.status_code == 409
        mock_task.delay.assert_not_called()

    @patch("core.tasks.gdpr.gdpr_anonymize_user")
    def test_anonymize_super_admin_returns_404(
        self, mock_task, client, db_session, admin_user,
        super_admin_user, auth_as, company
    ):
        """Super admins have no company_id, so they appear as 'not found'."""
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/gdpr/anonymize",
            json={
                "target_user_email": super_admin_user.email,
                "reason": "test",
            },
        )

        assert resp.status_code == 404
        mock_task.delay.assert_not_called()


class TestGdprCancelEndpoint:

    @patch("core.tasks.gdpr.gdpr_data_export")
    def test_cancel_pending_request(
        self, mock_task, client, db_session, admin_user,
        employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_task.delay.return_value = None

        # Create a request first
        create_resp = client.post(
            "/api/v1/audit/gdpr/export",
            json={"target_user_email": employee_user.email},
        )
        request_id = create_resp.json()["id"]

        # Cancel it
        resp = client.post(
            f"/api/v1/audit/gdpr/{request_id}/cancel"
        )

        assert resp.status_code == 200

    def test_cancel_nonexistent_returns_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/gdpr/01NONEXISTENT0000000000000/cancel"
        )

        assert resp.status_code == 404


class TestGdprDetailEndpoint:

    @patch("core.tasks.gdpr.gdpr_data_export")
    def test_get_request_detail(
        self, mock_task, client, db_session, admin_user,
        employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_task.delay.return_value = None

        # Create a request
        create_resp = client.post(
            "/api/v1/audit/gdpr/export",
            json={"target_user_email": employee_user.email},
        )
        request_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/audit/gdpr/{request_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == request_id
        assert data["request_type"] == "export"
        assert data["status"] == "pending"

    def test_get_nonexistent_returns_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get(
            "/api/v1/audit/gdpr/01NONEXISTENT0000000000000"
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Retention policy
# ---------------------------------------------------------------------------


class TestRetentionEndpoint:

    def test_get_retention_defaults(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/retention")

        assert resp.status_code == 200
        data = resp.json()
        assert data["retention_months"] == 36
        assert data["updated_at"] is None

    def test_update_retention(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            "/api/v1/audit/retention",
            json={"retention_months": 60},
        )

        assert resp.status_code == 200
        assert resp.json()["message"] == "Retention policy updated"

        # Verify
        get_resp = client.get("/api/v1/audit/retention")
        assert get_resp.json()["retention_months"] == 60

    def test_update_retention_invalid_period(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            "/api/v1/audit/retention",
            json={"retention_months": 15},
        )

        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------------


class TestVerifyIntegrityEndpoint:

    @patch("core.tasks.audit.verify_audit_integrity.delay")
    def test_request_verify(
        self,
        mock_delay,
        client,
        db_session,
        admin_user,
        auth_as,
        company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)
        mock_delay.return_value = MagicMock(id="task-123")

        resp = client.post(
            "/api/v1/audit/verify",
            json={},
        )

        assert resp.status_code == 202
        data = resp.json()
        assert data["task_id"] == "task-123"
        mock_delay.assert_called_once()
