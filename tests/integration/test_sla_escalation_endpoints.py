"""Integration tests for SLA escalation config + SLA status escalation (F3 - TASK-022)."""

import ulid

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetCriticality, AssetStatus
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.sla_bc.sla.domain.entities import SlaPolicy
from src.sla_bc.sla.infrastructure.repository import SlaRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_sla_policy(
    db_session,
    company_id: str,
    priority: str = "medium",
    name: str = "Medium policy",
    request_type: str | None = None,
    response_time_hours: float = 4,
    resolution_time_hours: float = 24,
) -> SlaPolicy:
    policy = SlaPolicy(
        id=str(ulid.new()),
        company_id=company_id,
        name=name,
        priority=priority,
        request_type=request_type,
        response_time_hours=response_time_hours,
        resolution_time_hours=resolution_time_hours,
        warning_threshold_pct=80,
        escalate_on_breach=False,
        is_active=True,
    )
    SlaRepository(db_session).save_policy(policy)
    db_session.flush()
    return policy


def _create_request(
    db_session,
    company_id: str,
    created_by: str,
    req_type: str = "incident",
) -> ServiceRequest:
    request = ServiceRequest.create(
        company_id=company_id,
        created_by=created_by,
        type=req_type,
        title="Test request",
        description="Test request description",
    )
    RequestRepository(db_session).save(request)
    db_session.flush()
    return request


def _create_asset(
    db_session,
    company_id: str,
    assigned_to: str,
    serial_number: str = "SN001",
    criticality: AssetCriticality = AssetCriticality.CRITICAL,
) -> Asset:
    asset = Asset(
        id=str(ulid.new()),
        company_id=company_id,
        type="laptop",
        brand="Dell",
        model="XPS 15",
        serial_number=serial_number,
        status=AssetStatus.ASSIGNED,
        assigned_to=assigned_to,
        criticality=criticality,
    )
    AssetRepository(db_session).save(asset)
    db_session.flush()
    return asset


# ---------------------------------------------------------------------------
# SLA Escalation Config Tests
# ---------------------------------------------------------------------------


def test_sla_escalation_config_get_default(
    client, db_session, company, admin_user, auth_as,
):
    """GET returns enabled=true when no config has been stored yet."""
    auth_as(admin_user)

    resp = client.get("/api/v1/settings/sla-escalation")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["enabled"] is True


def test_sla_escalation_config_put_save(
    client, db_session, company, admin_user, auth_as,
):
    """PUT with enabled=false saves and returns the updated value."""
    auth_as(admin_user)

    resp = client.put(
        "/api/v1/settings/sla-escalation",
        json={"enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False

    # Confirm GET reflects the change
    resp2 = client.get("/api/v1/settings/sla-escalation")
    assert resp2.status_code == 200
    assert resp2.json()["data"]["enabled"] is False


def test_sla_escalation_config_requires_admin(
    client, db_session, company, employee_user, auth_as,
):
    """GET as employee returns 403 Forbidden."""
    auth_as(employee_user)

    resp = client.get("/api/v1/settings/sla-escalation")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# SLA Status with Escalation Tests
# ---------------------------------------------------------------------------


def test_sla_status_escalated_with_critical_asset(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """
    When a request has affected assets with critical criticality,
    the SLA status should show escalated=true and effective_priority
    different from the original.

    Setup:
    - Create a request of type "configuration" (default priority LOW)
    - Create a CRITICAL asset assigned to the requester
    - PATCH affected-assets with that asset
    - Escalation: LOW -> MEDIUM (via PRIORITY_ESCALATION_MAP for critical)
    - Create an SLA policy matching the escalated priority "medium"
    """
    auth_as(technician_user)

    # Create SLA policy for the escalated priority "medium"
    _create_sla_policy(
        db_session, company.id,
        priority="medium",
        name="Medium SLA",
        response_time_hours=4,
        resolution_time_hours=24,
    )

    # Create a request with type "configuration" -> default priority LOW
    request = _create_request(
        db_session, company.id, employee_user.id, req_type="configuration",
    )

    # Create a CRITICAL asset assigned to the requester
    asset = _create_asset(
        db_session, company.id, employee_user.id,
        serial_number="ESCAL001", criticality=AssetCriticality.CRITICAL,
    )

    # Set affected assets
    patch_resp = client.patch(
        f"/api/v1/requests/{request.id}/affected-assets",
        json={"asset_ids": [asset.id]},
    )
    assert patch_resp.status_code == 200

    # Get SLA status
    resp = client.get(f"/api/v1/sla/requests/{request.id}/status")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data is not None
    assert data["escalated"] is True
    assert data["original_priority"] == "low"
    assert data["effective_priority"] == "medium"
    assert data["policy_name"] == "Medium SLA"


def test_sla_status_no_escalation_without_affected_assets(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """
    When a request has no affected assets, escalated should be false
    and effective_priority equals original_priority.
    """
    auth_as(technician_user)

    # Create SLA policy matching the default priority of a "configuration" request (low)
    _create_sla_policy(
        db_session, company.id,
        priority="low",
        name="Low SLA",
        response_time_hours=8,
        resolution_time_hours=48,
    )

    # Create a request of type "configuration" -> default priority LOW
    request = _create_request(
        db_session, company.id, employee_user.id, req_type="configuration",
    )

    # Get SLA status without setting any affected assets
    resp = client.get(f"/api/v1/sla/requests/{request.id}/status")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert data is not None
    assert data["escalated"] is False
    assert data["original_priority"] == "low"
    assert data["effective_priority"] == "low"
    assert data["policy_name"] == "Low SLA"
