"""Integration tests for /api/v1/reports endpoints (ADMIN)."""

import pytest
from unittest.mock import patch, MagicMock


class TestCreateReport:
    def test_create_report(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/reports", json={
            "type": "asset_inventory",
        })

        assert resp.status_code == 202
        data = resp.json()["data"]
        assert data["type"] == "asset_inventory"
        assert data["status"] == "pending"

    def test_create_report_with_parameters(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/reports", json={
            "type": "request_summary",
            "parameters": {"from_date": "2024-01-01", "to_date": "2024-12-31"},
        })

        assert resp.status_code == 202
        data = resp.json()["data"]
        assert data["parameters"]["from_date"] == "2024-01-01"

    def test_create_report_invalid_type(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/reports", json={"type": "invalid_type"})

        assert resp.status_code == 422


class TestListReports:
    def test_list_reports(self, client, auth_as, admin_user):
        auth_as(admin_user)
        client.post("/api/v1/reports", json={"type": "asset_inventory"})

        resp = client.get("/api/v1/reports")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    def test_list_reports_pagination(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/reports?page=1&page_size=5")

        assert resp.status_code == 200
        assert resp.json()["meta"]["page_size"] == 5


class TestGetReport:
    def test_get_report(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/reports", json={"type": "asset_inventory"})
        report_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}")

        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == report_id

    def test_get_report_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/reports/nonexistent")

        assert resp.status_code == 404


class TestDownloadReport:
    @patch("adapters.http.api.reports.routers.S3StorageService")
    def test_download_completed_report(self, mock_storage_cls, client, auth_as, admin_user, db_session):
        """Create a report, manually mark it completed with a storage key, then download."""
        from src.report_bc.report.domain.entities import Report
        from src.report_bc.report.domain.enums import ReportStatus
        from src.report_bc.report.infrastructure.repository import ReportRepository

        report = Report.create(
            company_id=admin_user.company_id,
            requested_by=admin_user.id,
            type="asset_inventory",
        )
        report.status = ReportStatus.COMPLETED
        report.storage_key = "reports/test-report.csv"
        ReportRepository(db_session).save(report)
        db_session.flush()

        mock_instance = MagicMock()
        mock_instance.get_signed_url.return_value = "https://s3.example.com/signed-url"
        mock_storage_cls.return_value = mock_instance

        auth_as(admin_user)
        resp = client.get(f"/api/v1/reports/{report.id}/download")

        assert resp.status_code == 200
        assert resp.json()["data"]["download_url"] == "https://s3.example.com/signed-url"

    def test_download_pending_report(self, client, auth_as, admin_user):
        auth_as(admin_user)
        create_resp = client.post("/api/v1/reports", json={"type": "asset_inventory"})
        report_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/reports/{report_id}/download")

        assert resp.status_code == 409


class TestDepartmentSpendingReport:
    def test_create_department_spending_report(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.post("/api/v1/reports", json={
            "type": "department_spending",
        })

        assert resp.status_code == 202
        data = resp.json()["data"]
        assert data["type"] == "department_spending"
        assert data["status"] == "pending"
