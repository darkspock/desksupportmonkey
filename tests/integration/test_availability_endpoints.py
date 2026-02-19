"""Integration tests for /api/v1/availability endpoints."""

import pytest


class TestSetAvailability:
    def test_set_availability_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.put(
            f"/api/v1/availability/technicians/{technician_user.id}",
            json={
                "windows": [
                    {
                        "day_of_week": 0,
                        "start_time": "09:00:00",
                        "end_time": "12:00:00",
                    },
                    {
                        "day_of_week": 0,
                        "start_time": "14:00:00",
                        "end_time": "17:00:00",
                    },
                    {
                        "day_of_week": 1,
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 3


class TestGetAvailability:
    def test_get_availability_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        # Set first
        client.put(
            f"/api/v1/availability/technicians/{technician_user.id}",
            json={
                "windows": [
                    {
                        "day_of_week": 2,
                        "start_time": "10:00:00",
                        "end_time": "16:00:00",
                    },
                ],
            },
        )
        # Then get
        resp = client.get(
            f"/api/v1/availability/technicians/{technician_user.id}",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1


class TestAddOverride:
    def test_add_override_201(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/availability/technicians/{technician_user.id}/overrides",
            json={
                "date": "2026-03-15",
                "is_available": False,
                "reason": "Vacation day",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["is_available"] is False
        assert data["reason"] == "Vacation day"


class TestListOverrides:
    def test_list_overrides_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        # Create an override first
        client.post(
            f"/api/v1/availability/technicians/{technician_user.id}/overrides",
            json={
                "date": "2026-04-01",
                "is_available": False,
                "reason": "Day off",
            },
        )
        resp = client.get(
            f"/api/v1/availability/technicians/{technician_user.id}/overrides",
            params={
                "date_from": "2026-03-01",
                "date_to": "2026-04-30",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1


class TestDeleteOverride:
    def test_delete_override_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        create_resp = client.post(
            f"/api/v1/availability/technicians/{technician_user.id}/overrides",
            json={
                "date": "2026-05-01",
                "is_available": False,
                "reason": "To be deleted",
            },
        )
        override_id = create_resp.json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/availability/overrides/{override_id}",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True

    def test_delete_override_404(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        resp = client.delete(
            "/api/v1/availability/overrides/nonexistent_id",
        )
        assert resp.status_code == 404


class TestGetAvailableSlots:
    def test_get_available_slots_200(
        self, client, auth_as, technician_user,
    ):
        auth_as(technician_user)
        # Query slots for a Monday (uses default windows)
        resp = client.get(
            f"/api/v1/availability/technicians/{technician_user.id}/slots",
            params={
                "date": "2026-03-02",
                "duration_minutes": 60,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["date"] == "2026-03-02"
        assert data["technician_id"] == technician_user.id
        assert data["duration_minutes"] == 60
        assert "slots" in data
        assert len(data["slots"]) >= 1


class TestSelfOnlyAccess:
    def test_technician_self_only_403(
        self, client, auth_as, technician_user, make_user,
    ):
        from src.auth_bc.user.domain.enums import UserRole

        other_tech = make_user(
            email="othertech@testco.com",
            role=UserRole.TECHNICIAN,
            company_id=technician_user.company_id,
        )

        auth_as(technician_user)
        resp = client.put(
            f"/api/v1/availability/technicians/{other_tech.id}",
            json={"windows": []},
        )
        assert resp.status_code == 403
