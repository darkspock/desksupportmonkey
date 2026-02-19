"""Integration tests for /api/v1/users endpoints (ADMIN)."""

import pytest
from unittest.mock import patch, MagicMock


class TestListUsers:
    def test_list_users(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/users")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 2  # admin + employee

    def test_list_users_filter_by_role(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/users?role=employee")

        assert resp.status_code == 200
        for u in resp.json()["data"]:
            assert u["role"] == "employee"

    def test_list_users_filter_active(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/users?is_active=true")

        assert resp.status_code == 200
        for u in resp.json()["data"]:
            assert u["is_active"] is True


class TestInviteUser:
    @patch("core.email.get_email_service")
    def test_invite_user(self, mock_email, client, auth_as, admin_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)

        resp = client.post("/api/v1/users/invite", json={"email": "newuser@testco.com"})

        assert resp.status_code == 201
        assert resp.json()["data"]["message"] == "Invitation sent"

    @patch("core.email.get_email_service")
    def test_invite_wrong_domain(self, mock_email, client, auth_as, admin_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)

        resp = client.post("/api/v1/users/invite", json={"email": "user@wrong.com"})

        assert resp.status_code == 403


class TestGetUser:
    def test_get_user(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.get(f"/api/v1/users/{employee_user.id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == employee_user.email

    def test_get_user_not_found(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.get("/api/v1/users/nonexistent")

        assert resp.status_code == 404


class TestChangeRole:
    @patch("core.email.get_email_service")
    def test_change_role(self, mock_email, client, auth_as, admin_user, employee_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{employee_user.id}/role", json={"role": "technician"})

        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "technician"

    @patch("core.email.get_email_service")
    def test_cannot_change_own_role(self, mock_email, client, auth_as, admin_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{admin_user.id}/role", json={"role": "employee"})

        assert resp.status_code == 409

    @patch("core.email.get_email_service")
    def test_cannot_assign_super_admin(self, mock_email, client, auth_as, admin_user, employee_user):
        mock_email.return_value = MagicMock()
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{employee_user.id}/role", json={"role": "super_admin"})

        assert resp.status_code == 403


class TestDeactivateUser:
    def test_deactivate_user(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{employee_user.id}/deactivate")

        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_cannot_deactivate_self(self, client, auth_as, admin_user):
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{admin_user.id}/deactivate")

        assert resp.status_code == 409


class TestActivateUser:
    def test_activate_user(self, client, auth_as, admin_user, employee_user, db_session):
        auth_as(admin_user)
        # First deactivate
        client.patch(f"/api/v1/users/{employee_user.id}/deactivate")

        resp = client.patch(f"/api/v1/users/{employee_user.id}/activate")

        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is True


class TestAssignDepartment:
    def test_assign_department(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)
        # Create a department first
        dept_resp = client.post("/api/v1/departments", json={"name": "IT"})
        dept_id = dept_resp.json()["data"]["id"]

        resp = client.patch(f"/api/v1/users/{employee_user.id}/department", json={
            "department_id": dept_id,
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["department_id"] == dept_id

    def test_assign_nonexistent_department(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{employee_user.id}/department", json={
            "department_id": "nonexistent",
        })

        assert resp.status_code == 404

    def test_unassign_department(self, client, auth_as, admin_user, employee_user):
        auth_as(admin_user)

        resp = client.patch(f"/api/v1/users/{employee_user.id}/department", json={
            "department_id": None,
        })

        assert resp.status_code == 200
        assert resp.json()["data"]["department_id"] is None
