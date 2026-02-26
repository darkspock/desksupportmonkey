"""Integration tests for /api/v1/checkouts and /api/v1/my/custody endpoints."""

import pytest

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetStatus
from src.asset_bc.asset.infrastructure.repository import AssetRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_asset(db_session, company_id, **overrides):
    defaults = dict(
        company_id=company_id, type="laptop",
        brand="Dell", model="Latitude 5540", serial_number="SN-INT-001",
    )
    defaults.update(overrides)
    asset = Asset.create(**defaults)
    repo = AssetRepository(db_session)
    repo.save(asset)
    db_session.flush()
    return asset


def _create_assigned_asset(db_session, company_id, user_id, **overrides):
    asset = _create_asset(db_session, company_id, **overrides)
    asset.assign(user_id=user_id, department_id=None)
    AssetRepository(db_session).save(asset)
    db_session.flush()
    return asset


# ---------------------------------------------------------------------------
# POST /api/v1/checkouts/assets/{asset_id} — Create checkout
# ---------------------------------------------------------------------------


class TestCreateCheckout:
    def test_checkout_assigned_asset(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-CO-001")
        auth_as(technician_user)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["asset_id"] == asset.id
        assert data["user_id"] == employee_user.id
        assert data["condition_out"] == "good"
        assert data["status"] == "open"
        assert data["auto_assigned"] is False

    def test_checkout_in_stock_auto_assigns(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_asset(db_session, company.id, serial_number="SN-CO-002")
        assert asset.status == AssetStatus.IN_STOCK
        auth_as(technician_user)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "new",
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["auto_assigned"] is True

        # Asset should now be assigned
        db_session.refresh(db_session.get(
            __import__("src.asset_bc.asset.infrastructure.models", fromlist=["AssetModel"]).AssetModel,
            asset.id,
        ))

    def test_checkout_not_found_asset(self, client, auth_as, technician_user, employee_user):
        auth_as(technician_user)
        resp = client.post("/api/v1/checkouts/assets/nonexistent", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })
        assert resp.status_code == 404

    def test_duplicate_active_checkout_rejected(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-CO-003")
        auth_as(technician_user)

        # First checkout
        resp1 = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })
        assert resp1.status_code == 201

        # Second checkout should fail
        resp2 = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "fair",
        })
        assert resp2.status_code == 409

    def test_employee_cannot_create_checkout(self, client, auth_as, employee_user, db_session, company):
        asset = _create_asset(db_session, company.id, serial_number="SN-CO-004")
        auth_as(employee_user)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/checkouts/assets/{asset_id}/checkin — Check in
# ---------------------------------------------------------------------------


class TestCheckin:
    def _checkout_asset(self, client, asset_id, user_id):
        return client.post(f"/api/v1/checkouts/assets/{asset_id}", json={
            "user_id": user_id,
            "condition_out": "good",
        })

    def test_checkin_happy_path(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-CI-001")
        auth_as(technician_user)
        self._checkout_asset(client, asset.id, employee_user.id)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/checkin", json={
            "condition_in": "fair",
            "notes_in": "Some wear",
        })

        assert resp.status_code == 200

    def test_checkin_no_active_checkout(self, client, auth_as, technician_user, db_session, company):
        asset = _create_asset(db_session, company.id, serial_number="SN-CI-002")
        auth_as(technician_user)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/checkin", json={
            "condition_in": "good",
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/checkouts/assets/{asset_id}/cancel — Cancel
# ---------------------------------------------------------------------------


class TestCancelCheckout:
    def test_cancel_happy_path(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-CL-001")
        auth_as(technician_user)
        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/cancel", json={
            "reason": "Wrong equipment",
        })
        assert resp.status_code == 200

    def test_cancel_no_checkout(self, client, auth_as, technician_user, db_session, company):
        asset = _create_asset(db_session, company.id, serial_number="SN-CL-002")
        auth_as(technician_user)

        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/cancel", json={
            "reason": "test",
        })
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/checkouts/assets/{asset_id}/accept — Accept (employee)
# ---------------------------------------------------------------------------


class TestAcceptCheckout:
    def test_accept_happy_path(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-AC-001")
        auth_as(technician_user)
        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        # Switch to employee
        auth_as(employee_user)
        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/accept")
        assert resp.status_code == 200

    def test_accept_wrong_user(self, client, auth_as, technician_user, employee_user, make_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-AC-002")
        auth_as(technician_user)
        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        # Different employee tries to accept
        from src.auth_bc.user.domain.enums import UserRole
        other = make_user("other@testco.com", role=UserRole.EMPLOYEE, company_id=company.id)
        auth_as(other)
        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/accept")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/checkouts/assets/{asset_id}/current — Current checkout
# ---------------------------------------------------------------------------


class TestGetCurrentCheckout:
    def test_returns_current(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-GC-001")
        auth_as(technician_user)
        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}/current")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["asset_id"] == asset.id
        assert data["status"] == "open"

    def test_returns_null_when_none(self, client, auth_as, technician_user, db_session, company):
        asset = _create_asset(db_session, company.id, serial_number="SN-GC-002")
        auth_as(technician_user)

        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}/current")
        assert resp.status_code == 200
        assert resp.json()["data"] is None


# ---------------------------------------------------------------------------
# GET /api/v1/checkouts/assets/{asset_id} — Asset checkout history
# ---------------------------------------------------------------------------


class TestListAssetCheckouts:
    def test_paginated_list(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-LA-001")
        auth_as(technician_user)

        # Create and checkin a checkout
        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        assert "meta" in data
        assert data["meta"]["total"] >= 1


# ---------------------------------------------------------------------------
# GET /api/v1/checkouts — Company-wide checkouts
# ---------------------------------------------------------------------------


class TestListCompanyCheckouts:
    def test_lists_open_checkouts(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-LC-001")
        auth_as(technician_user)

        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        resp = client.get("/api/v1/checkouts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1


# ---------------------------------------------------------------------------
# Full lifecycle: checkout → accept → checkin
# ---------------------------------------------------------------------------


class TestCheckoutLifecycle:
    def test_full_lifecycle(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-FL-001")
        auth_as(technician_user)

        # 1. Checkout
        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "new",
            "notes_out": "Fresh from stock",
        })
        assert resp.status_code == 201
        checkout_data = resp.json()["data"]
        assert checkout_data["status"] == "open"

        # 2. Accept (as employee)
        auth_as(employee_user)
        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/accept")
        assert resp.status_code == 200

        # Verify accepted
        auth_as(technician_user)
        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}/current")
        current = resp.json()["data"]
        assert current["status"] == "accepted"
        assert current["accepted_at"] is not None

        # 3. Checkin
        resp = client.post(f"/api/v1/checkouts/assets/{asset.id}/checkin", json={
            "condition_in": "good",
            "notes_in": "Returned in good condition",
        })
        assert resp.status_code == 200

        # 4. No more active checkout
        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}/current")
        assert resp.json()["data"] is None

        # 5. History shows completed checkout
        resp = client.get(f"/api/v1/checkouts/assets/{asset.id}")
        assert resp.json()["meta"]["total"] >= 1


# ---------------------------------------------------------------------------
# My custody endpoints
# ---------------------------------------------------------------------------


class TestMyCustody:
    def test_get_my_custody(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-MC-001")
        auth_as(technician_user)

        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        auth_as(employee_user)
        resp = client.get("/api/v1/my/custody")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "pending_acceptance" in data
        assert "open" in data
        # Should be in pending_acceptance since not yet accepted
        assert len(data["pending_acceptance"]) >= 1

    def test_my_accept_equipment(self, client, auth_as, technician_user, employee_user, db_session, company):
        asset = _create_assigned_asset(db_session, company.id, employee_user.id, serial_number="SN-MC-002")
        auth_as(technician_user)

        client.post(f"/api/v1/checkouts/assets/{asset.id}", json={
            "user_id": employee_user.id,
            "condition_out": "good",
        })

        auth_as(employee_user)
        resp = client.post(f"/api/v1/my/equipment/{asset.id}/accept")
        assert resp.status_code == 200
