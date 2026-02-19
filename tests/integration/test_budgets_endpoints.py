"""Integration tests for budget endpoints."""

import pytest


@pytest.fixture()
def department(client, auth_as, admin_user):
    """Create a department for budget tests."""
    auth_as(admin_user)
    resp = client.post(
        "/api/v1/departments",
        json={"name": "BudgetDept"},
    )
    return resp.json()["data"]


class TestSetBudget:
    def test_set_budget_returns_200(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 500000,
                "fiscal_year": 2026,
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["allocated_amount_cents"] == 500000
        assert data["spent_cents"] == 0
        assert data["remaining_cents"] == 500000
        assert data["utilization_pct"] == 0.0

    def test_set_budget_updates_existing(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)
        client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 500000,
                "fiscal_year": 2026,
            },
        )

        resp = client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 800000,
                "fiscal_year": 2026,
            },
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["allocated_amount_cents"] == 800000

    def test_negative_budget_returns_422(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)

        resp = client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": -100,
                "fiscal_year": 2026,
            },
        )

        assert resp.status_code == 422

    def test_non_admin_returns_403(
        self, client, auth_as, technician_user, department,
    ):
        auth_as(technician_user)

        resp = client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 500000,
                "fiscal_year": 2026,
            },
        )

        assert resp.status_code == 403


class TestGetBudget:
    def test_get_budget_returns_200(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)
        client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 300000,
                "fiscal_year": 2026,
            },
        )

        resp = client.get(
            f"/api/v1/departments/{department['id']}/budget?fiscal_year=2026",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["allocated_amount_cents"] == 300000

    def test_get_budget_no_budget_returns_404(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)

        resp = client.get(
            f"/api/v1/departments/{department['id']}/budget?fiscal_year=2099",
        )

        assert resp.status_code == 404


class TestGetBudgetSummary:
    def test_summary_returns_200(
        self, client, auth_as, admin_user, department,
    ):
        auth_as(admin_user)
        client.put(
            f"/api/v1/departments/{department['id']}/budget",
            json={
                "allocated_amount_cents": 200000,
                "fiscal_year": 2026,
            },
        )

        resp = client.get(
            "/api/v1/budgets/summary?fiscal_year=2026",
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["fiscal_year"] == 2026
        assert data["total_allocated_cents"] >= 200000
        assert len(data["departments"]) >= 1
