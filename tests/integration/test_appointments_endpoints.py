"""Integration tests for /api/v1/appointments endpoints."""

from datetime import datetime, timezone

import pytest


def _create_request(client):
    """Create a service request and return its ID."""
    resp = client.post("/api/v1/requests", json={
        "type": "incident",
        "title": "Test incident for appointment",
        "description": "Test description",
    })
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_appointment(
    client, request_id, technician_id, employee_id,
    start="2026-03-10T10:00:00Z", duration=60,
):
    """Create an appointment and return the response."""
    return client.post("/api/v1/appointments", json={
        "request_id": request_id,
        "technician_id": technician_id,
        "employee_id": employee_id,
        "scheduled_start": start,
        "duration_minutes": duration,
    })


class TestCreateAppointment:
    def test_create_appointment_201(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "CONFIRMED"
        assert data["request_id"] == request_id
        assert data["duration_minutes"] == 60

    def test_create_overlap_409(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        resp1 = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-11T10:00:00Z",
        )
        assert resp1.status_code == 201

        # Same time slot → 409
        resp2 = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-11T10:00:00Z",
        )
        assert resp2.status_code == 409


class TestListAppointments:
    def test_list_appointments_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-12T10:00:00Z",
        )

        resp = client.get("/api/v1/appointments")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1

    def test_list_appointments_filters_by_datetime_range(
        self, client, auth_as, technician_user, employee_user,
    ):
        """Date range filters should include appointments inside the window."""
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client,
            request_id,
            technician_user.id,
            employee_user.id,
            start="2026-02-26T16:01:00Z",
        )
        assert create_resp.status_code == 201
        created_id = create_resp.json()["data"]["id"]

        resp = client.get(
            "/api/v1/appointments",
            params={
                "page": 1,
                "page_size": 100,
                "date_from": "2026-02-23T00:00:00",
                "date_to": "2026-03-01T23:59:59",
            },
        )
        assert resp.status_code == 200
        body = resp.json()

        assert body["meta"]["total"] >= 1
        returned_ids = {item["id"] for item in body["data"]}
        assert created_id in returned_ids


class TestGetAppointment:
    def test_get_appointment_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-13T10:00:00Z",
        )
        appt_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/appointments/{appt_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == appt_id


class TestConfirmAppointment:
    def test_confirm_appointment_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        # Employee creates → PENDING
        auth_as(employee_user)
        request_id = _create_request(client)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-14T10:00:00Z",
        )
        assert create_resp.status_code == 201
        appt_id = create_resp.json()["data"]["id"]
        assert create_resp.json()["data"]["status"] == "PENDING"

        # Technician confirms
        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/appointments/{appt_id}/confirm",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CONFIRMED"


class TestCancelAppointment:
    def test_cancel_appointment_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-15T10:00:00Z",
        )
        appt_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/appointments/{appt_id}/cancel",
            json={"reason": "No longer needed"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CANCELLED"
        assert resp.json()["data"]["cancellation_reason"] == "No longer needed"


class TestCompleteAppointment:
    def test_complete_appointment_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-16T10:00:00Z",
        )
        appt_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/appointments/{appt_id}/complete",
            json={"notes": "Resolved the issue"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "COMPLETED"
        assert resp.json()["data"]["notes"] == "Resolved the issue"


class TestRescheduleAppointment:
    def test_reschedule_appointment_201(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-17T10:00:00Z",
        )
        old_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/appointments/{old_id}/reschedule",
            json={
                "new_start": "2026-03-18T14:00:00Z",
                "new_duration_minutes": 60,
                "reason": "Client requested different time",
            },
        )
        assert resp.status_code == 201
        new_data = resp.json()["data"]
        assert new_data["id"] != old_id
        assert new_data["status"] == "CONFIRMED"
        assert new_data["rescheduled_from_id"] == old_id


class TestMyAppointments:
    def test_my_appointments_200(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-19T10:00:00Z",
        )

        auth_as(employee_user)
        resp = client.get("/api/v1/my/appointments")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 1


class TestRequestCascade:
    def test_resolve_request_cancels_appointments(
        self, client, auth_as, technician_user, employee_user,
    ):
        auth_as(employee_user)
        request_id = _create_request(client)

        auth_as(technician_user)
        create_resp = _create_appointment(
            client, request_id,
            technician_user.id, employee_user.id,
            start="2026-03-20T10:00:00Z",
        )
        appt_id = create_resp.json()["data"]["id"]

        # Assign first so we can transition to in_progress
        client.patch(
            f"/api/v1/requests/{request_id}/assign",
            json={"assigned_to": technician_user.id},
        )
        # Move to in_review → in_progress → resolved
        client.patch(
            f"/api/v1/requests/{request_id}/status",
            json={"status": "in_review"},
        )
        client.patch(
            f"/api/v1/requests/{request_id}/status",
            json={"status": "in_progress"},
        )
        resp = client.patch(
            f"/api/v1/requests/{request_id}/status",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200

        # Appointment should be auto-cancelled
        appt_resp = client.get(
            f"/api/v1/appointments/{appt_id}",
        )
        assert appt_resp.status_code == 200
        assert appt_resp.json()["data"]["status"] == "CANCELLED"
        assert "resolved" in appt_resp.json()["data"]["cancellation_reason"]
