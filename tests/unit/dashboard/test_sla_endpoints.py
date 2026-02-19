from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.dashboard import routers as dashboard_routers
from adapters.http.api.dashboard.dependencies import get_request_repo
from app import app
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _admin_user():
    return User.create(
        email="admin@test.com",
        role=UserRole.ADMIN,
        company_id="comp1",
    )


@pytest.fixture
def mock_request_repo():
    return MagicMock()


@pytest.fixture
def admin_client(mock_request_repo):
    admin = _admin_user()
    app.dependency_overrides[dashboard_routers.admin_dep] = lambda: admin
    app.dependency_overrides[get_request_repo] = lambda: mock_request_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestSlaAlerts:
    def test_returns_sla_alerts(self, admin_client, mock_request_repo):
        mock_request_repo.find_open_requests_with_age.return_value = [
            {
                "id": "req1", "title": "Broken laptop", "type": "incident",
                "priority": "urgent", "status": "submitted",
                "assigned_to": "tech1",
                "created_at": datetime(2026, 2, 15, 10, 0, tzinfo=timezone.utc),
                "hours_open": 10.0,
            },
            {
                "id": "req2", "title": "New mouse", "type": "new_equipment",
                "priority": "low", "status": "in_progress",
                "assigned_to": None,
                "created_at": datetime(2026, 2, 14, 10, 0, tzinfo=timezone.utc),
                "hours_open": 2.0,
            },
        ]

        response = admin_client.get("/api/v1/dashboard/alerts/sla")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

        # Urgent with 10 hours open > 4 hour threshold = breached
        assert data[0]["id"] == "req1"
        assert data[0]["sla_threshold_hours"] == 4
        assert data[0]["breached"] is True

        # Low with 2 hours open < 168 hour threshold = not breached
        assert data[1]["id"] == "req2"
        assert data[1]["sla_threshold_hours"] == 168
        assert data[1]["breached"] is False

    def test_empty_returns_empty(self, admin_client, mock_request_repo):
        mock_request_repo.find_open_requests_with_age.return_value = []

        response = admin_client.get("/api/v1/dashboard/alerts/sla")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_sla_thresholds_values(self):
        assert dashboard_routers.SLA_THRESHOLDS_HOURS == {
            "urgent": 4,
            "high": 24,
            "medium": 72,
            "low": 168,
        }

    def test_all_priorities_have_thresholds(self, admin_client, mock_request_repo):
        mock_request_repo.find_open_requests_with_age.return_value = [
            {
                "id": f"req-{p}", "title": f"Test {p}", "type": "incident",
                "priority": p, "status": "submitted",
                "assigned_to": None,
                "created_at": datetime(2026, 2, 15, tzinfo=timezone.utc),
                "hours_open": 100.0,
            }
            for p in ["low", "medium", "high", "urgent"]
        ]

        response = admin_client.get("/api/v1/dashboard/alerts/sla")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 4
        thresholds = {item["priority"]: item["sla_threshold_hours"] for item in data}
        assert thresholds == {"urgent": 4, "high": 24, "medium": 72, "low": 168}
