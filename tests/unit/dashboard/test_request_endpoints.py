from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.dashboard import routers as dashboard_routers
from app import app
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _admin_user():
    return User.create(
        email="admin@test.com",
        role=UserRole.ADMIN,
        company_id="comp1",
    )


def _employee_user():
    return User.create(
        email="emp@test.com",
        role=UserRole.EMPLOYEE,
        company_id="comp1",
    )


@pytest.fixture
def admin_client():
    admin = _admin_user()
    app.dependency_overrides[dashboard_routers.admin_dep] = lambda: admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def employee_client():
    from fastapi import HTTPException, status

    def _employee_dep():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    app.dependency_overrides[dashboard_routers.admin_dep] = _employee_dep
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestRequestSummary:
    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_returns_summary(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.count_by_status.return_value = {
            "submitted": 5, "in_review": 2, "in_progress": 3, "resolved": 10, "rejected": 1,
        }
        repo_instance.count_by_type.return_value = {
            "incident": 12, "new_equipment": 5, "onboarding": 4,
        }
        repo_instance.count_by_priority.return_value = {
            "low": 3, "medium": 5, "high": 8, "urgent": 5,
        }

        response = admin_client.get("/api/v1/dashboard/requests/summary")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_open"] == 10
        assert data["total_resolved"] == 10
        assert data["by_status"]["submitted"] == 5
        assert data["by_type"]["incident"] == 12
        assert data["by_priority"]["urgent"] == 5

    def test_forbidden_for_employee(self, employee_client):
        response = employee_client.get("/api/v1/dashboard/requests/summary")
        assert response.status_code == 403


class TestResolutionTime:
    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_returns_resolution_time(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.avg_resolution_time.return_value = 18.5
        repo_instance.avg_resolution_time_by_technician.return_value = [
            {"technician_id": "tech1", "avg_hours": 12.0, "resolved_count": 5},
        ]

        response = admin_client.get("/api/v1/dashboard/requests/resolution-time")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["avg_hours"] == 18.5
        assert len(data["by_technician"]) == 1
        assert data["by_technician"][0]["technician_id"] == "tech1"

    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_with_date_params(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.avg_resolution_time.return_value = 10.0
        repo_instance.avg_resolution_time_by_technician.return_value = []

        response = admin_client.get(
            "/api/v1/dashboard/requests/resolution-time?from_date=2026-01-01&to_date=2026-01-31"
        )
        assert response.status_code == 200

    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_null_avg_hours(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.avg_resolution_time.return_value = None
        repo_instance.avg_resolution_time_by_technician.return_value = []

        response = admin_client.get("/api/v1/dashboard/requests/resolution-time")
        assert response.status_code == 200
        assert response.json()["data"]["avg_hours"] is None


class TestRequestTrend:
    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_returns_trend_data(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.count_by_period.return_value = [
            {"period": "2026-01-01T00:00:00+00:00", "type": "incident", "count": 3},
            {"period": "2026-01-01T00:00:00+00:00", "type": "onboarding", "count": 1},
            {"period": "2026-01-02T00:00:00+00:00", "type": "incident", "count": 2},
        ]

        response = admin_client.get("/api/v1/dashboard/requests/trend")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["bucket"] == "day"
        assert len(data["data"]) == 2
        assert data["data"][0]["total"] == 4
        assert data["data"][0]["by_type"]["incident"] == 3

    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_with_bucket_param(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.count_by_period.return_value = []

        response = admin_client.get("/api/v1/dashboard/requests/trend?bucket=week")
        assert response.status_code == 200
        assert response.json()["data"]["bucket"] == "week"

    @patch("adapters.http.api.dashboard.routers.RequestRepository")
    def test_empty_trend(self, MockRepo, admin_client):
        repo_instance = MockRepo.return_value
        repo_instance.count_by_period.return_value = []

        response = admin_client.get("/api/v1/dashboard/requests/trend")
        assert response.status_code == 200
        assert response.json()["data"]["data"] == []
