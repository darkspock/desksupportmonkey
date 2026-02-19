"""Integration tests for /api/v1/my endpoints (mixed auth)."""

import pytest


class TestMyEquipment:
    def test_my_equipment_empty(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.get("/api/v1/my/equipment")

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_my_equipment_with_assigned_asset(self, client, auth_as, technician_user, employee_user):
        # Create and assign an asset
        auth_as(technician_user)
        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "XPS", "serial_number": "MYEQ001",
        })
        asset_id = create_resp.json()["data"]["id"]
        client.patch(f"/api/v1/assets/{asset_id}/assign", json={"user_id": employee_user.id})

        # Check my equipment as employee
        auth_as(employee_user)
        resp = client.get("/api/v1/my/equipment")

        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["serial_number"] == "MYEQ001"


class TestMyRequests:
    def test_my_requests_empty(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.get("/api/v1/my/requests")

        assert resp.status_code == 200
        assert resp.json()["data"] == []
        assert resp.json()["meta"]["total"] == 0

    def test_my_requests_with_data(self, client, auth_as, employee_user):
        auth_as(employee_user)
        client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "My issue",
            "description": "Something broke",
        })

        resp = client.get("/api/v1/my/requests")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1


class TestMyNotifications:
    def test_list_notifications_empty(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.get("/api/v1/my/notifications")

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_notifications_with_data(self, client, auth_as, employee_user, db_session):
        """Create a notification directly in DB, then list."""
        from src.notification_bc.notification.domain.entities import Notification
        from src.notification_bc.notification.infrastructure.repository import NotificationRepository

        n = Notification.create(
            user_id=employee_user.id,
            company_id=employee_user.company_id,
            event_type="request.created",
            title="New request",
            body="A new request was created",
        )
        NotificationRepository(db_session).save(n)
        db_session.flush()

        auth_as(employee_user)
        resp = client.get("/api/v1/my/notifications")

        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1
        assert "unread_count" in resp.json()["meta"]


class TestMarkNotificationRead:
    def test_mark_read(self, client, auth_as, employee_user, db_session):
        from src.notification_bc.notification.domain.entities import Notification
        from src.notification_bc.notification.infrastructure.repository import NotificationRepository

        n = Notification.create(
            user_id=employee_user.id,
            company_id=employee_user.company_id,
            event_type="request.created",
            title="Test",
            body="Test body",
        )
        NotificationRepository(db_session).save(n)
        db_session.flush()

        auth_as(employee_user)
        resp = client.patch(f"/api/v1/my/notifications/{n.id}/read")

        assert resp.status_code == 200
        assert resp.json()["data"]["is_read"] is True

    def test_mark_read_not_found(self, client, auth_as, employee_user):
        auth_as(employee_user)

        resp = client.patch("/api/v1/my/notifications/nonexistent/read")

        assert resp.status_code == 404


class TestMarkAllNotificationsRead:
    def test_mark_all_read(self, client, auth_as, employee_user, db_session):
        from src.notification_bc.notification.domain.entities import Notification
        from src.notification_bc.notification.infrastructure.repository import NotificationRepository

        repo = NotificationRepository(db_session)
        for i in range(3):
            n = Notification.create(
                user_id=employee_user.id,
                company_id=employee_user.company_id,
                event_type="test.event",
                title=f"Notif {i}",
                body=f"Body {i}",
            )
            repo.save(n)
        db_session.flush()

        auth_as(employee_user)
        resp = client.patch("/api/v1/my/notifications/read-all")

        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is True


class TestMyCompanySettings:
    def test_get_company_settings(self, client, auth_as, admin_user, company):
        auth_as(admin_user)

        resp = client.get("/api/v1/my/company-settings")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == company.id
        assert data["name"] == company.name
        assert "testco.com" in data["email_domains"]

    def test_update_company_settings(self, client, auth_as, admin_user, company):
        auth_as(admin_user)

        resp = client.put("/api/v1/my/company-settings", json={
            "email_domains": ["testco.com", "testco.org"],
        })

        assert resp.status_code == 200
        assert "testco.org" in resp.json()["data"]["email_domains"]
