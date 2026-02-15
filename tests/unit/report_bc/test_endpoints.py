from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.reports import routers as report_routers
from app import app
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus, ReportType


def _admin_user():
    return User.create(
        email="admin@test.com",
        role=UserRole.ADMIN,
        company_id="comp1",
    )


def _make_report(**overrides):
    defaults = dict(
        company_id="comp1",
        requested_by="user1",
        type="asset_inventory",
    )
    defaults.update(overrides)
    return Report.create(**defaults)


@pytest.fixture
def admin_client():
    admin = _admin_user()
    app.dependency_overrides[report_routers.admin_dep] = lambda: admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def employee_client():
    from fastapi import HTTPException, status

    def _deny():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    app.dependency_overrides[report_routers.admin_dep] = _deny
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCreateReport:
    @patch("adapters.http.api.reports.routers.ReportRepository")
    @patch("core.tasks.reports.generate_report")
    def test_returns_202(self, mock_task, MockRepo, admin_client):
        report = _make_report()
        MockRepo.return_value.save.return_value = report

        response = admin_client.post(
            "/api/v1/reports",
            json={"type": "asset_inventory"},
        )
        assert response.status_code == 202
        data = response.json()["data"]
        assert data["type"] == "asset_inventory"
        assert data["status"] == "pending"

    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_invalid_type_returns_422(self, MockRepo, admin_client):
        response = admin_client.post(
            "/api/v1/reports",
            json={"type": "invalid"},
        )
        assert response.status_code == 422

    def test_forbidden_for_employee(self, employee_client):
        response = employee_client.post(
            "/api/v1/reports",
            json={"type": "asset_inventory"},
        )
        assert response.status_code == 403


class TestListReports:
    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_returns_list(self, MockRepo, admin_client):
        reports = [_make_report() for _ in range(2)]
        MockRepo.return_value.find_all.return_value = (reports, 2)

        response = admin_client.get("/api/v1/reports")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2
        assert response.json()["meta"]["total"] == 2


class TestGetReport:
    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_returns_detail(self, MockRepo, admin_client):
        report = _make_report()
        MockRepo.return_value.find_by_id.return_value = report

        response = admin_client.get(f"/api/v1/reports/{report.id}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == report.id

    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_not_found(self, MockRepo, admin_client):
        MockRepo.return_value.find_by_id.return_value = None

        response = admin_client.get("/api/v1/reports/nonexistent")
        assert response.status_code == 404


class TestDownloadReport:
    @patch("adapters.http.api.reports.routers.S3StorageService")
    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_returns_signed_url(self, MockRepo, MockS3, admin_client):
        report = _make_report()
        report.status = ReportStatus.COMPLETED
        report.storage_key = f"reports/comp1/{report.id}.pdf"
        MockRepo.return_value.find_by_id.return_value = report
        MockS3.return_value.get_signed_url.return_value = "https://s3.example.com/signed"

        response = admin_client.get(f"/api/v1/reports/{report.id}/download")
        assert response.status_code == 200
        assert response.json()["data"]["download_url"] == "https://s3.example.com/signed"

    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_not_found(self, MockRepo, admin_client):
        MockRepo.return_value.find_by_id.return_value = None

        response = admin_client.get("/api/v1/reports/nonexistent/download")
        assert response.status_code == 404

    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_pending_returns_409(self, MockRepo, admin_client):
        report = _make_report()
        MockRepo.return_value.find_by_id.return_value = report

        response = admin_client.get(f"/api/v1/reports/{report.id}/download")
        assert response.status_code == 409

    @patch("adapters.http.api.reports.routers.ReportRepository")
    def test_failed_returns_409(self, MockRepo, admin_client):
        report = _make_report()
        report.status = ReportStatus.FAILED
        MockRepo.return_value.find_by_id.return_value = report

        response = admin_client.get(f"/api/v1/reports/{report.id}/download")
        assert response.status_code == 409

    def test_forbidden_for_employee(self, employee_client):
        response = employee_client.get("/api/v1/reports/someid/download")
        assert response.status_code == 403
