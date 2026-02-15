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


@pytest.fixture
def admin_client():
    admin = _admin_user()
    app.dependency_overrides[dashboard_routers.admin_dep] = lambda: admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAssetSummary:
    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_returns_summary(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.count_by_status.return_value = {
            "in_stock": 10, "assigned": 15, "in_repair": 2, "decommissioned": 3,
        }
        repo.count_by_type.return_value = {
            "laptop": 12, "monitor": 8, "keyboard": 5, "mouse": 3,
            "headset": 1, "docking_station": 0, "other": 1,
        }

        response = admin_client.get("/api/v1/dashboard/assets/summary")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 30
        assert data["by_status"]["in_stock"] == 10
        assert data["by_type"]["laptop"] == 12


class TestWarrantyAlerts:
    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_returns_warranty_alerts(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.find_expiring_warranties.return_value = [
            {
                "id": "asset1", "brand": "Dell", "model": "Latitude",
                "serial_number": "SN001", "warranty_expiration": "2026-03-01",
                "assigned_to": "user1", "days_remaining": 13,
            },
        ]

        response = admin_client.get("/api/v1/dashboard/alerts/warranty")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["brand"] == "Dell"
        assert data[0]["days_remaining"] == 13

    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_custom_days_param(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.find_expiring_warranties.return_value = []

        response = admin_client.get("/api/v1/dashboard/alerts/warranty?days=90")
        assert response.status_code == 200
        repo.find_expiring_warranties.assert_called_once_with("comp1", 90)

    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_empty_list(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.find_expiring_warranties.return_value = []

        response = admin_client.get("/api/v1/dashboard/alerts/warranty")
        assert response.status_code == 200
        assert response.json()["data"] == []


class TestAgingAlerts:
    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_returns_aging_alerts(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.find_aging_assets.return_value = [
            {
                "id": "asset1", "brand": "Dell", "model": "Latitude",
                "serial_number": "SN001", "purchase_date": "2021-01-15",
                "age_years": 5.1, "assigned_to": "user1",
            },
        ]

        response = admin_client.get("/api/v1/dashboard/alerts/aging")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["age_years"] == 5.1

    @patch("adapters.http.api.dashboard.routers.AssetRepository")
    def test_custom_years_param(self, MockRepo, admin_client):
        repo = MockRepo.return_value
        repo.find_aging_assets.return_value = []

        response = admin_client.get("/api/v1/dashboard/alerts/aging?years=5")
        assert response.status_code == 200
        repo.find_aging_assets.assert_called_once_with("comp1", 5)
