"""Integration tests for support ticket endpoints (customer + super admin)."""

from unittest.mock import patch

import pytest


def _create_ticket(client, **overrides):
    defaults = {
        "category": "bug_report",
        "subject": "Test bug",
        "description": "Something is broken",
    }
    defaults.update(overrides)
    return client.post("/api/v1/my/support-tickets", json=defaults)


# ---------------------------------------------------------------------------
# Customer endpoints (/api/v1/my/support-tickets)
# ---------------------------------------------------------------------------


class TestCustomerCreateTicket:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_create_ticket_returns_201(self, mock_email, client, auth_as, technician_user, db_session):
        # Create the sequence if not exists
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        resp = _create_ticket(client)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["reference"].startswith("SUP-")
        assert data["status"] == "open"
        assert data["priority"] == "medium"
        assert data["category"] == "bug_report"
        assert data["subject"] == "Test bug"

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_create_ticket_sends_emails(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client)

        # Should send 2 emails: creator confirmation + support team notification
        assert mock_email.delay.call_count == 2

    def test_create_ticket_missing_fields_returns_422(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.post("/api/v1/my/support-tickets", json={})

        assert resp.status_code == 422

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_create_ticket_with_ai_summary(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        resp = _create_ticket(
            client,
            ai_conversation_summary="AI could not resolve the issue",
        )

        assert resp.status_code == 201
        assert resp.json()["data"]["ai_conversation_summary"] == "AI could not resolve the issue"


class TestCustomerListTickets:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_my_tickets(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client, subject="Ticket A")
        _create_ticket(client, subject="Ticket B")

        resp = client.get("/api/v1/my/support-tickets")

        assert resp.status_code == 200
        data = resp.json()["data"]
        meta = resp.json()["meta"]
        assert len(data) == 2
        assert meta["total"] == 2

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_filter_by_status(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client, subject="Open ticket")

        resp = client.get("/api/v1/my/support-tickets?status=open")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert all(t["status"] == "open" for t in data)


class TestCustomerTicketDetail:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_get_ticket_detail(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/my/support-tickets/{ticket_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == ticket_id
        assert data["messages"] == []

    def test_get_nonexistent_ticket_returns_404(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.get("/api/v1/my/support-tickets/nonexistent")

        assert resp.status_code == 404

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_tenant_isolation(self, mock_email, client, auth_as, technician_user, make_user, company, db_session):
        """A technician from another company cannot see this company's tickets."""
        from src.auth_bc.user.domain.enums import UserRole
        from src.company_bc.company.domain.entities import Company
        from src.company_bc.company.infrastructure.repository import CompanyRepository

        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        # Create ticket as technician
        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        # Create other company + user
        other_company = Company.create(name="Other Co", email_domains=["otherco.com"])
        other_company.slug = Company.generate_slug(other_company.name)
        CompanyRepository(db_session).save(other_company)
        db_session.flush()

        other_tech = make_user(
            email="tech@otherco.com",
            role=UserRole.TECHNICIAN,
            company_id=other_company.id,
        )

        # Attempt to access ticket from other company
        auth_as(other_tech)
        resp = client.get(f"/api/v1/my/support-tickets/{ticket_id}")

        assert resp.status_code == 404


class TestCustomerAddMessage:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_add_message(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/my/support-tickets/{ticket_id}/messages",
            json={"body": "I have more details to share"},
        )

        assert resp.status_code == 201


class TestCustomerReopenTicket:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_reopen_resolved_ticket(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        # Resolve the ticket via super admin
        auth_as(super_admin_user)
        client.patch(
            f"/api/v1/support-tickets/{ticket_id}/status",
            json={"status": "resolved"},
        )

        # Reopen as customer
        auth_as(technician_user)
        resp = client.post(f"/api/v1/my/support-tickets/{ticket_id}/reopen")

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "open"


class TestCustomerRating:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_submit_rating_returns_201(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        # Resolve via super admin
        auth_as(super_admin_user)
        client.patch(f"/api/v1/support-tickets/{ticket_id}/status", json={"status": "resolved"})

        # Rate as customer
        auth_as(technician_user)
        resp = client.post(
            f"/api/v1/my/support-tickets/{ticket_id}/rating",
            json={"rating": 5, "comment": "Great support!"},
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["satisfaction_rating"] == 5
        assert data["satisfaction_comment"] == "Great support!"
        assert data["rated_at"] is not None

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_duplicate_rating_returns_409(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        client.patch(f"/api/v1/support-tickets/{ticket_id}/status", json={"status": "resolved"})

        auth_as(technician_user)
        client.post(f"/api/v1/my/support-tickets/{ticket_id}/rating", json={"rating": 5})

        resp = client.post(f"/api/v1/my/support-tickets/{ticket_id}/rating", json={"rating": 3})
        assert resp.status_code == 409

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_rating_on_open_ticket_returns_409(self, mock_email, client, auth_as, technician_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        resp = client.post(f"/api/v1/my/support-tickets/{ticket_id}/rating", json={"rating": 5})
        assert resp.status_code == 409

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_rating_fields_in_detail_response(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        client.patch(f"/api/v1/support-tickets/{ticket_id}/status", json={"status": "resolved"})

        auth_as(technician_user)
        client.post(f"/api/v1/my/support-tickets/{ticket_id}/rating", json={"rating": 4})

        resp = client.get(f"/api/v1/my/support-tickets/{ticket_id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["satisfaction_rating"] == 4
        assert data["rated_at"] is not None

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_stats_include_avg_satisfaction(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        client.patch(f"/api/v1/support-tickets/{ticket_id}/status", json={"status": "resolved"})

        auth_as(technician_user)
        client.post(f"/api/v1/my/support-tickets/{ticket_id}/rating", json={"rating": 4})

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "avg_satisfaction_rating" in data
        assert data["avg_satisfaction_rating"] is not None


# ---------------------------------------------------------------------------
# Super admin endpoints (/api/v1/support-tickets)
# ---------------------------------------------------------------------------


class TestSuperAdminListTickets:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_all_tickets(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client, subject="Ticket 1")

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets")

        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_with_search(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client, subject="Unique searchable title")

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets?search=searchable")

        assert resp.status_code == 200


class TestSuperAdminListSortAndFilter:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_with_sort_by_created_at_asc(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client, subject="First ticket")
        _create_ticket(client, subject="Second ticket")

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets?sort_by=created_at&sort_order=asc")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 2
        # ASC order: first created should appear first
        dates = [d["created_at"] for d in data]
        assert dates == sorted(dates)

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_with_invalid_sort_by_falls_back(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client)

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets?sort_by=invalid_column")

        assert resp.status_code == 200  # Should not error, falls back to default

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_response_includes_company_id(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client)

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert "company_id" in data[0]
        assert data[0]["company_id"] is not None

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_list_response_includes_created_by_email(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client)

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert "created_by_email" in data[0]
        assert data[0]["created_by_email"] is not None


class TestSuperAdminStats:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_get_stats(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        _create_ticket(client)

        auth_as(super_admin_user)
        resp = client.get("/api/v1/support-tickets/stats")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "open" in data
        assert "total" in data
        assert data["total"] >= 1


class TestSuperAdminDetail:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    def test_get_detail_cross_company(self, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.get(f"/api/v1/support-tickets/{ticket_id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == ticket_id


class TestSuperAdminAddMessage:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_add_platform_message(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.post(
            f"/api/v1/support-tickets/{ticket_id}/messages",
            json={"body": "We are looking into this."},
        )

        assert resp.status_code == 201


class TestSuperAdminChangeStatus:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_change_status_to_resolved(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/support-tickets/{ticket_id}/status",
            json={"status": "resolved"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "resolved"

    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_invalid_status_transition_returns_409(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        # Close it first
        auth_as(super_admin_user)
        client.patch(
            f"/api/v1/support-tickets/{ticket_id}/status",
            json={"status": "closed"},
        )

        # Try to reopen (CLOSED → OPEN is not valid)
        resp = client.patch(
            f"/api/v1/support-tickets/{ticket_id}/status",
            json={"status": "open"},
        )

        assert resp.status_code == 409


class TestSuperAdminChangePriority:
    @patch("adapters.http.api.my.support_router.send_support_ticket_email")
    @patch("adapters.http.api.support.router.send_support_ticket_email")
    def test_change_priority(self, mock_admin_email, mock_email, client, auth_as, technician_user, super_admin_user, db_session):
        db_session.execute(
            __import__("sqlalchemy").text(
                "CREATE SEQUENCE IF NOT EXISTS support_ticket_ref_seq START 1"
            )
        )
        db_session.flush()

        auth_as(technician_user)
        create_resp = _create_ticket(client)
        ticket_id = create_resp.json()["data"]["id"]

        auth_as(super_admin_user)
        resp = client.patch(
            f"/api/v1/support-tickets/{ticket_id}/priority",
            json={"priority": "urgent"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["priority"] == "urgent"
