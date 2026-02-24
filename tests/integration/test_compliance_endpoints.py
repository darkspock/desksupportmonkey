"""Integration tests for compliance assessment, evidence, and dashboard endpoints."""
import pytest
from unittest.mock import patch, MagicMock

from src.audit_bc.audit.domain.entities import ComplianceControl
from src.audit_bc.audit.infrastructure.repository import AuditRepository


@pytest.fixture()
def compliance_control(db_session, company):
    """Create a custom compliance control for testing."""
    control = ComplianceControl.create(
        company_id=company.id,
        code="COMP-001",
        name="Test Compliance Control",
        framework="NIS2",
        description="A control for compliance tests",
    )
    repo = AuditRepository(db_session)
    repo.save_control(control)
    db_session.flush()
    return control


@pytest.fixture()
def second_control(db_session, company):
    """Create a second control in a different framework."""
    control = ComplianceControl.create(
        company_id=company.id,
        code="DORA-T01",
        name="DORA Test Control",
        framework="DORA",
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
    from datetime import datetime, timezone
    from src.company_bc.company.infrastructure.models import CompanyModel

    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(trial_ends_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    )
    db_session.flush()


# ---------------------------------------------------------------------------
# Assessment CRUD
# ---------------------------------------------------------------------------


class TestComplianceAssessmentEndpoints:

    def test_assess_control(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "compliant", "notes": "Fully compliant"},
        )

        assert resp.status_code == 200
        assert resp.json()["message"] == "Assessment updated"

    def test_assess_control_returns_404_for_unknown_control(
        self, client, db_session, admin_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            "/api/v1/audit/compliance/controls/01NONEXISTENT0000000000000/assessment",
            json={"status": "compliant"},
        )

        assert resp.status_code == 404

    def test_assess_control_returns_422_for_invalid_status(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "invalid_status"},
        )

        assert resp.status_code == 422

    def test_list_assessments(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Assess the control first
        client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "partial", "notes": "Work in progress"},
        )

        resp = client.get("/api/v1/audit/compliance/assessments")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        ctrl_item = next(
            (c for c in data if c["control_id"] == compliance_control.id),
            None,
        )
        assert ctrl_item is not None
        assert ctrl_item["status"] == "partial"
        assert ctrl_item["notes"] == "Work in progress"

    def test_list_assessments_with_framework_filter(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control, second_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get(
            "/api/v1/audit/compliance/assessments?framework=NIS2"
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        frameworks = {c["framework"] for c in data}
        assert "DORA" not in frameworks

    def test_assess_returns_403_for_employee(
        self, client, db_session, employee_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(employee_user)

        resp = client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "compliant"},
        )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Evidence CRUD
# ---------------------------------------------------------------------------


class TestComplianceEvidenceEndpoints:

    def test_add_evidence(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence",
            json={
                "evidence_type": "manual",
                "title": "SOC2 Report",
                "description": "Annual audit",
                "url": "https://example.com/soc2.pdf",
            },
        )

        assert resp.status_code == 201
        assert resp.json()["message"] == "Evidence added"

    def test_add_evidence_returns_404_for_unknown_control(
        self, client, db_session, admin_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            "/api/v1/audit/compliance/controls/01NONEXISTENT0000000000000/evidence",
            json={
                "evidence_type": "manual",
                "title": "Some evidence",
            },
        )

        assert resp.status_code == 404

    def test_list_evidence(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Add evidence first
        client.post(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence",
            json={
                "evidence_type": "manual",
                "title": "Test Evidence",
            },
        )

        resp = client.get(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence"
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["title"] == "Test Evidence"
        assert data[0]["evidence_type"] == "manual"

    def test_remove_evidence(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Add evidence first
        client.post(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence",
            json={
                "evidence_type": "audit_log",
                "title": "Log evidence",
                "reference_id": "01ENTRY000000000000000000001",
            },
        )

        # Get evidence list to find the ID
        resp = client.get(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence"
        )
        evidence_id = resp.json()["data"][0]["id"]

        # Remove
        resp = client.delete(
            f"/api/v1/audit/compliance/evidence/{evidence_id}"
        )

        assert resp.status_code == 200
        assert resp.json()["message"] == "Evidence removed"

        # Verify removed
        resp = client.get(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence"
        )
        assert len(resp.json()["data"]) == 0

    def test_remove_nonexistent_evidence_returns_404(
        self, client, db_session, admin_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.delete(
            "/api/v1/audit/compliance/evidence/01NONEXISTENT0000000000000"
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestComplianceDashboardEndpoints:

    def test_get_dashboard(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/compliance/dashboard")

        assert resp.status_code == 200
        data = resp.json()
        assert "overall_compliance_pct" in data
        assert "total_controls" in data
        assert "compliant" in data
        assert "frameworks" in data
        assert "gap_controls" in data
        assert data["total_controls"] >= 1

    def test_dashboard_with_framework_filter(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control, second_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get(
            "/api/v1/audit/compliance/dashboard?framework=NIS2"
        )

        assert resp.status_code == 200
        data = resp.json()
        frameworks = [f["framework"] for f in data["frameworks"]]
        assert "NIS2" in frameworks
        assert "DORA" not in frameworks

    def test_dashboard_reflects_assessment(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Assess as compliant
        client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "compliant"},
        )

        resp = client.get("/api/v1/audit/compliance/dashboard")

        assert resp.status_code == 200
        data = resp.json()
        assert data["compliant"] >= 1

    def test_dashboard_returns_403_for_employee(
        self, client, db_session, employee_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(employee_user)

        resp = client.get("/api/v1/audit/compliance/dashboard")

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestComplianceExportEndpoints:

    @patch("core.tasks.compliance.generate_compliance_report")
    def test_trigger_export(
        self, mock_task, client, db_session, admin_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        mock_result = MagicMock()
        mock_result.id = "test-task-id-123"
        mock_task.delay.return_value = mock_result

        resp = client.post(
            "/api/v1/audit/compliance/export",
            json={},
        )

        assert resp.status_code == 202
        assert resp.json()["task_id"] == "test-task-id-123"

    @patch("core.tasks.compliance.generate_compliance_report")
    def test_trigger_export_with_framework(
        self, mock_task, client, db_session, admin_user, auth_as, company,
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        mock_result = MagicMock()
        mock_result.id = "test-task-id-456"
        mock_task.delay.return_value = mock_result

        resp = client.post(
            "/api/v1/audit/compliance/export",
            json={"framework": "NIS2"},
        )

        assert resp.status_code == 202
        mock_task.delay.assert_called_once_with(
            company_id=company.id,
            requested_by=admin_user.id,
            framework="NIS2",
        )


# ---------------------------------------------------------------------------
# Plan gating (free plan = 402)
# ---------------------------------------------------------------------------


class TestCompliancePlanGating:

    def test_assessments_returns_402_on_free_plan(
        self, client, db_session, admin_user, auth_as, company,
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/compliance/assessments")

        assert resp.status_code == 402

    def test_assess_control_returns_402_on_free_plan(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/assessment",
            json={"status": "compliant"},
        )

        assert resp.status_code == 402

    def test_dashboard_returns_402_on_free_plan(
        self, client, db_session, admin_user, auth_as, company,
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)

        resp = client.get("/api/v1/audit/compliance/dashboard")

        assert resp.status_code == 402

    def test_add_evidence_returns_402_on_free_plan(
        self, client, db_session, admin_user, auth_as, company,
        compliance_control,
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            f"/api/v1/audit/compliance/controls/{compliance_control.id}/evidence",
            json={"evidence_type": "manual", "title": "Test"},
        )

        assert resp.status_code == 402
