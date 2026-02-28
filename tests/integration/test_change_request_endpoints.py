"""Integration tests for /api/v1/changes endpoints."""

BASE = "/api/v1/changes"


def _create_change(client, **overrides):
    payload = {"title": "Install security patch", "change_type": "standard"}
    payload.update(overrides)
    return client.post(BASE, json=payload)


def _submit(client, change_id):
    return client.post(f"{BASE}/{change_id}/submit")


def _approve(client, change_id, **overrides):
    payload = {}
    payload.update(overrides)
    return client.post(f"{BASE}/{change_id}/approve", json=payload)


def _reject(client, change_id, reason="Not justified"):
    return client.post(f"{BASE}/{change_id}/reject", json={"reason": reason})


def _start(client, change_id):
    return client.post(f"{BASE}/{change_id}/start")


def _implement(client, change_id, **overrides):
    payload = {}
    payload.update(overrides)
    return client.post(f"{BASE}/{change_id}/implement", json=payload)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestChangeRequestCRUD:
    def test_create_standard(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_change(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Install security patch"
        assert data["status"] == "draft"
        assert data["change_type"] == "standard"
        assert data["requested_by"] == technician_user.id

    def test_create_normal(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_change(client, change_type="normal")
        assert resp.status_code == 201
        assert resp.json()["change_type"] == "normal"

    def test_create_emergency(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = _create_change(client, change_type="emergency")
        assert resp.status_code == 201
        assert resp.json()["change_type"] == "emergency"

    def test_get_detail(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        get_resp = client.get(f"{BASE}/{change_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == change_id
        assert "timeline" in data
        assert len(data["timeline"]) >= 1  # CREATED event

    def test_get_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.get(f"{BASE}/nonexistent")
        assert resp.status_code == 404

    def test_list_change_requests(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_change(client, title="Change A")
        _create_change(client, title="Change B")

        resp = client.get(BASE)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["total"] >= 2

    def test_list_filter_by_status(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_change(client)  # draft

        resp = client.get(f"{BASE}?status=draft")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["status"] == "draft"

    def test_list_filter_by_type(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_change(client, change_type="emergency")

        resp = client.get(f"{BASE}?type=emergency")
        assert resp.status_code == 200
        for item in resp.json()["data"]:
            assert item["change_type"] == "emergency"

    def test_list_search(self, client, auth_as, technician_user):
        auth_as(technician_user)
        _create_change(client, title="UniqueSearchTerm7890")

        resp = client.get(f"{BASE}?search=UniqueSearchTerm7890")
        assert resp.status_code == 200
        assert any(
            "UniqueSearchTerm7890" in c["title"] for c in resp.json()["data"]
        )

    def test_update_in_draft(self, client, auth_as, technician_user):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        update_resp = client.patch(
            f"{BASE}/{change_id}",
            json={
                "title": "Updated title",
                "description": "New description",
                "business_justification": "Cost savings",
                "risk_assessment": "Low risk",
                "rollback_plan": "Restore from backup",
            },
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["title"] == "Updated title"
        assert data["description"] == "New description"
        assert data["business_justification"] == "Cost savings"
        assert data["risk_assessment"] == "Low risk"
        assert data["rollback_plan"] == "Restore from backup"

    def test_update_not_found(self, client, auth_as, technician_user):
        auth_as(technician_user)
        resp = client.patch(
            f"{BASE}/nonexistent", json={"title": "X"}
        )
        assert resp.status_code == 404

    def test_update_in_non_editable_state(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        _submit(client, change_id)  # standard → SCHEDULED

        resp = client.patch(
            f"{BASE}/{change_id}", json={"title": "Should fail"}
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# State Machine — Submit
# ---------------------------------------------------------------------------


class TestSubmitChangeRequest:
    def test_submit_standard_auto_approves(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        resp = _submit(client, change_id)
        assert resp.status_code == 200
        assert resp.json()["status"] == "scheduled"

    def test_submit_normal_pending_approval(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client, change_type="normal")
        change_id = create_resp.json()["id"]

        # First add rollback plan
        client.patch(
            f"{BASE}/{change_id}",
            json={"rollback_plan": "Restore from backup"},
        )

        resp = _submit(client, change_id)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_approval"

    def test_submit_normal_without_rollback_plan_fails(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client, change_type="normal")
        change_id = create_resp.json()["id"]

        resp = _submit(client, change_id)
        assert resp.status_code == 422

    def test_submit_emergency_without_rollback_plan_fails(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client, change_type="emergency")
        change_id = create_resp.json()["id"]

        resp = _submit(client, change_id)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# State Machine — Approve / Reject
# ---------------------------------------------------------------------------


class TestApproveRejectChangeRequest:
    def _create_pending(self, client, auth_as, technician_user, admin_user):
        """Helper to create a normal change in PENDING_APPROVAL."""
        auth_as(technician_user)
        create_resp = _create_change(client, change_type="normal")
        change_id = create_resp.json()["id"]
        client.patch(
            f"{BASE}/{change_id}",
            json={"rollback_plan": "Restore from backup"},
        )
        _submit(client, change_id)
        return change_id

    def test_admin_approves(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = self._create_pending(
            client, auth_as, technician_user, admin_user
        )
        auth_as(admin_user)
        resp = _approve(client, change_id, notes="Looks good")
        assert resp.status_code == 200
        assert resp.json()["status"] == "scheduled"
        assert resp.json()["approved_by"] == admin_user.id

    def test_technician_cannot_approve(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = self._create_pending(
            client, auth_as, technician_user, admin_user
        )
        auth_as(technician_user)
        resp = _approve(client, change_id)
        assert resp.status_code == 403

    def test_admin_rejects_with_reason(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = self._create_pending(
            client, auth_as, technician_user, admin_user
        )
        auth_as(admin_user)
        resp = _reject(client, change_id, reason="Too risky")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
        assert resp.json()["rejection_reason"] == "Too risky"

    def test_technician_cannot_reject(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = self._create_pending(
            client, auth_as, technician_user, admin_user
        )
        auth_as(technician_user)
        resp = _reject(client, change_id)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# State Machine — Start / Implement / Rollback / Close
# ---------------------------------------------------------------------------


class TestChangeLifecycle:
    def _create_scheduled(self, client, auth_as, technician_user):
        """Helper: standard change → SCHEDULED."""
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]
        _submit(client, change_id)
        return change_id

    def test_start_change(self, client, auth_as, technician_user):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        resp = _start(client, change_id)
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"
        assert resp.json()["started_at"] is not None

    def test_start_from_draft_fails(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        resp = _start(client, change_id)
        assert resp.status_code == 422

    def test_implement_change(self, client, auth_as, technician_user):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)

        resp = _implement(client, change_id, notes="All systems nominal")
        assert resp.status_code == 200
        assert resp.json()["status"] == "implemented"
        assert resp.json()["implementation_notes"] == "All systems nominal"

    def test_implement_without_notes(
        self, client, auth_as, technician_user
    ):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)

        resp = _implement(client, change_id)
        assert resp.status_code == 200
        assert resp.json()["status"] == "implemented"
        assert resp.json()["implementation_notes"] is None

    def test_rollback_from_in_progress(
        self, client, auth_as, technician_user
    ):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)

        resp = client.post(
            f"{BASE}/{change_id}/rollback",
            json={"reason": "Deployment failed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rolled_back"
        assert resp.json()["rollback_reason"] == "Deployment failed"

    def test_rollback_from_implemented(
        self, client, auth_as, technician_user
    ):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)
        _implement(client, change_id)

        resp = client.post(
            f"{BASE}/{change_id}/rollback",
            json={"reason": "Issues found post-implementation"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rolled_back"

    def test_close_change(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)
        _implement(client, change_id)

        auth_as(admin_user)
        resp = client.post(f"{BASE}/{change_id}/close")
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"
        assert resp.json()["closed_at"] is not None

    def test_technician_cannot_close(
        self, client, auth_as, technician_user
    ):
        change_id = self._create_scheduled(
            client, auth_as, technician_user
        )
        _start(client, change_id)
        _implement(client, change_id)

        resp = client.post(f"{BASE}/{change_id}/close")
        assert resp.status_code == 403

    def test_invalid_transition_returns_422(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        # DRAFT → close is invalid
        auth_as(technician_user)
        resp = _implement(client, change_id)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Assign
# ---------------------------------------------------------------------------


class TestAssignChange:
    def test_assign_in_draft(
        self, client, auth_as, technician_user, admin_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        auth_as(admin_user)
        resp = client.post(
            f"{BASE}/{change_id}/assign",
            json={"assigned_to": technician_user.id},
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == technician_user.id

    def test_assign_in_scheduled(
        self, client, auth_as, technician_user, admin_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]
        _submit(client, change_id)

        auth_as(admin_user)
        resp = client.post(
            f"{BASE}/{change_id}/assign",
            json={"assigned_to": technician_user.id},
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == technician_user.id

    def test_technician_cannot_assign(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        resp = client.post(
            f"{BASE}/{change_id}/assign",
            json={"assigned_to": "someone"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


class TestChangeTimeline:
    def test_timeline_records_events(
        self, client, auth_as, technician_user, admin_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        # Submit
        _submit(client, change_id)
        # Start
        _start(client, change_id)
        # Implement
        _implement(client, change_id)

        detail = client.get(f"{BASE}/{change_id}")
        events = detail.json()["timeline"]
        event_types = [e["event_type"] for e in events]
        assert "created" in event_types
        assert "submitted" in event_types
        assert "started" in event_types
        assert "implemented" in event_types


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


class TestChangeAuthorization:
    def test_employee_cannot_create(
        self, client, auth_as, employee_user
    ):
        auth_as(employee_user)
        resp = _create_change(client)
        assert resp.status_code == 403

    def test_employee_cannot_list(
        self, client, auth_as, employee_user
    ):
        auth_as(employee_user)
        resp = client.get(BASE)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------


class TestMultiTenantIsolation:
    def test_cannot_see_other_company_changes(
        self, client, auth_as, technician_user, make_user, db_session
    ):
        from src.company_bc.company.domain.entities import Company
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        from src.auth_bc.user.domain.enums import UserRole

        # Create change with technician_user
        auth_as(technician_user)
        create_resp = _create_change(client, title="Company A change")
        assert create_resp.status_code == 201

        # Create another company + user
        other_company = Company.create(
            name="Other Corp", email_domains=["othercorp.com"]
        )
        CompanyRepository(db_session).save(other_company)
        db_session.flush()

        other_tech = make_user(
            email="tech@othercorp.com",
            role=UserRole.TECHNICIAN,
            company_id=other_company.id,
        )

        # List changes as other company user — should not see Company A's changes
        auth_as(other_tech)
        resp = client.get(BASE)
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 0


# ---------------------------------------------------------------------------
# Asset Linking
# ---------------------------------------------------------------------------


def _create_asset(client, serial_number, brand="Dell", model="Latitude"):
    """Helper to create an asset and return its ID."""
    resp = client.post("/api/v1/assets", json={
        "type": "laptop",
        "brand": brand,
        "model": model,
        "serial_number": serial_number,
    })
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _close_change(client, auth_as, technician_user, admin_user, change_id):
    """Helper: drive a standard change through the full lifecycle to CLOSED."""
    auth_as(technician_user)
    _submit(client, change_id)   # standard → SCHEDULED
    _start(client, change_id)    # → IN_PROGRESS
    _implement(client, change_id)  # → IMPLEMENTED
    auth_as(admin_user)
    client.post(f"{BASE}/{change_id}/close")  # → CLOSED


class TestAssetLinking:
    def test_link_assets_success(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "LINK001")

        resp = client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )
        assert resp.status_code == 204

    def test_link_assets_duplicates_skipped(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "LINK002")

        # First link
        resp1 = client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )
        assert resp1.status_code == 204

        # Second link of the same asset — should succeed silently
        resp2 = client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )
        assert resp2.status_code == 204

    def test_link_assets_terminal_state_rejected(
        self, client, auth_as, technician_user, admin_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "LINK003")

        # Drive the change to CLOSED (terminal state)
        _close_change(client, auth_as, technician_user, admin_user, change_id)

        # Try to link — should fail because status is terminal
        auth_as(technician_user)
        resp = client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )
        assert resp.status_code == 422

    def test_link_assets_change_not_found(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        _create_asset(client, "LINK004")

        resp = client.post(
            f"{BASE}/nonexistent-change-id/assets",
            json={"asset_ids": ["some-asset-id"]},
        )
        assert resp.status_code == 404

    def test_unlink_asset_success(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "UNLINK001")

        # Link first
        client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )

        # Unlink
        resp = client.delete(f"{BASE}/{change_id}/assets/{asset_id}")
        assert resp.status_code == 204

    def test_unlink_asset_status_guard(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "UNLINK002")

        # Link the asset
        client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )

        # Move to IN_PROGRESS (submit → SCHEDULED, start → IN_PROGRESS)
        _submit(client, change_id)
        _start(client, change_id)

        # Try to unlink — should fail; only DRAFT/PENDING_APPROVAL/SCHEDULED allowed
        resp = client.delete(f"{BASE}/{change_id}/assets/{asset_id}")
        assert resp.status_code == 422

    def test_detail_includes_affected_assets(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(
            client, "DETAIL001", brand="HP", model="EliteBook"
        )

        # Link asset
        client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )

        # Get detail
        detail_resp = client.get(f"{BASE}/{change_id}")
        assert detail_resp.status_code == 200

        data = detail_resp.json()
        assert "affected_assets" in data
        assert len(data["affected_assets"]) == 1

        linked = data["affected_assets"][0]
        assert linked["asset_id"] == asset_id
        assert linked["asset_brand"] == "HP"
        assert linked["asset_model"] == "EliteBook"

    def test_link_creates_change_event(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        asset_id = _create_asset(client, "EVENT001")

        # Link asset
        client.post(
            f"{BASE}/{change_id}/assets",
            json={"asset_ids": [asset_id]},
        )

        # Get detail and check timeline
        detail_resp = client.get(f"{BASE}/{change_id}")
        assert detail_resp.status_code == 200

        events = detail_resp.json()["timeline"]
        event_types = [e["event_type"] for e in events]
        assert "asset_linked" in event_types


# ---------------------------------------------------------------------------
# Post-Implementation Review (F2)
# ---------------------------------------------------------------------------


def _create_pir(client, change_id, **overrides):
    payload = {"outcome": "successful"}
    payload.update(overrides)
    return client.post(f"{BASE}/{change_id}/pir", json=payload)


def _drive_standard_to_implemented(client, auth_as, technician_user):
    """Helper: create a standard change and drive it to IMPLEMENTED."""
    auth_as(technician_user)
    create_resp = _create_change(client)
    change_id = create_resp.json()["id"]
    _submit(client, change_id)   # standard → SCHEDULED
    _start(client, change_id)    # → IN_PROGRESS
    _implement(client, change_id)  # → IMPLEMENTED
    return change_id


def _drive_emergency_to_implemented(
    client, auth_as, technician_user, admin_user
):
    """Helper: create an emergency change and drive it to IMPLEMENTED."""
    auth_as(technician_user)
    create_resp = _create_change(client, change_type="emergency")
    change_id = create_resp.json()["id"]
    client.patch(
        f"{BASE}/{change_id}",
        json={"rollback_plan": "Restore from backup"},
    )
    _submit(client, change_id)       # → PENDING_APPROVAL
    auth_as(admin_user)
    _approve(client, change_id)      # → SCHEDULED
    auth_as(technician_user)
    _start(client, change_id)        # → IN_PROGRESS
    _implement(client, change_id)    # → IMPLEMENTED
    return change_id


class TestPostImplementationReview:
    def test_create_pir_happy_path(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_standard_to_implemented(
            client, auth_as, technician_user
        )

        auth_as(admin_user)
        resp = _create_pir(
            client,
            change_id,
            outcome="successful",
            issues_found="None",
            lessons_learned="Went smoothly",
            follow_up_actions="Monitor for 24h",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pir"] is not None
        assert data["pir"]["outcome"] == "successful"
        assert data["pir"]["issues_found"] == "None"
        assert data["pir"]["lessons_learned"] == "Went smoothly"
        assert data["pir"]["follow_up_actions"] == "Monitor for 24h"
        assert data["pir"]["created_by"] == admin_user.id

    def test_create_pir_duplicate_returns_409(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_standard_to_implemented(
            client, auth_as, technician_user
        )

        auth_as(admin_user)
        first = _create_pir(client, change_id)
        assert first.status_code == 200

        second = _create_pir(client, change_id)
        assert second.status_code == 409

    def test_create_pir_invalid_status_returns_422(
        self, client, auth_as, technician_user, admin_user
    ):
        # Create a change in DRAFT status (not IMPLEMENTED)
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        auth_as(admin_user)
        resp = _create_pir(client, change_id)
        assert resp.status_code == 422

    def test_create_pir_not_found_returns_404(
        self, client, auth_as, admin_user
    ):
        auth_as(admin_user)
        resp = _create_pir(client, "nonexistent-change-id")
        assert resp.status_code == 404

    def test_close_emergency_without_pir_returns_422(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_emergency_to_implemented(
            client, auth_as, technician_user, admin_user
        )

        auth_as(admin_user)
        resp = client.post(f"{BASE}/{change_id}/close")
        assert resp.status_code == 422

    def test_close_emergency_with_pir_succeeds(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_emergency_to_implemented(
            client, auth_as, technician_user, admin_user
        )

        auth_as(admin_user)
        pir_resp = _create_pir(client, change_id)
        assert pir_resp.status_code == 200

        close_resp = client.post(f"{BASE}/{change_id}/close")
        assert close_resp.status_code == 200
        assert close_resp.json()["status"] == "closed"
        assert close_resp.json()["closed_at"] is not None

    def test_close_standard_without_pir_succeeds(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_standard_to_implemented(
            client, auth_as, technician_user
        )

        auth_as(admin_user)
        resp = client.post(f"{BASE}/{change_id}/close")
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    def test_detail_includes_pir_when_exists(
        self, client, auth_as, technician_user, admin_user
    ):
        change_id = _drive_standard_to_implemented(
            client, auth_as, technician_user
        )

        auth_as(admin_user)
        _create_pir(
            client,
            change_id,
            outcome="partial",
            issues_found="Minor config drift",
        )

        detail_resp = client.get(f"{BASE}/{change_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["pir"] is not None
        assert data["pir"]["outcome"] == "partial"
        assert data["pir"]["issues_found"] == "Minor config drift"
        assert "id" in data["pir"]
        assert "created_at" in data["pir"]

    def test_detail_pir_null_when_none(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        create_resp = _create_change(client)
        change_id = create_resp.json()["id"]

        detail_resp = client.get(f"{BASE}/{change_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["pir"] is None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestChangeDashboard:
    def test_admin_gets_dashboard(self, client, auth_as, admin_user):
        auth_as(admin_user)
        resp = client.get(f"{BASE}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_open" in data
        assert "pending_approval" in data
        assert "in_progress" in data
        assert "implemented" in data
        assert "scheduled_this_week" in data
        assert "status_counts" in data
        assert "type_counts" in data
        assert "upcoming_scheduled" in data
        assert "recently_implemented" in data
        assert "rolled_back_90_days" in data
        assert isinstance(data["status_counts"], dict)
        assert isinstance(data["type_counts"], dict)

    def test_non_admin_gets_403(
        self, client, auth_as, technician_user
    ):
        auth_as(technician_user)
        resp = client.get(f"{BASE}/dashboard")
        assert resp.status_code == 403

    def test_dashboard_with_data(
        self, client, auth_as, admin_user, technician_user
    ):
        # Create a standard change and submit it (auto-schedules)
        auth_as(technician_user)
        r = _create_change(client, change_type="standard")
        assert r.status_code == 201
        cid = r.json()["id"]
        _submit(client, cid)

        auth_as(admin_user)
        resp = client.get(f"{BASE}/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status_counts"]["scheduled"] >= 1

    def test_dashboard_counts_are_non_negative(
        self, client, auth_as, admin_user
    ):
        auth_as(admin_user)
        resp = client.get(f"{BASE}/dashboard")
        data = resp.json()
        assert data["total_open"] >= 0
        assert data["rolled_back_90_days"] >= 0
        for v in data["status_counts"].values():
            assert v >= 0
