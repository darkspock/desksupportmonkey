"""Integration tests for affected assets endpoints (F3 - TASK-022)."""

import ulid

from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.domain.enums import AssetCriticality, AssetStatus
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.infrastructure.repository import RequestRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _create_request(db_session, company_id: str, created_by: str) -> ServiceRequest:
    request = ServiceRequest.create(
        company_id=company_id,
        created_by=created_by,
        type="incident",
        title="Test incident",
        description="Test incident description",
    )
    RequestRepository(db_session).save(request)
    db_session.flush()
    return request


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_patch_sets_affected_assets(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """PATCH with valid asset IDs returns 200 and sets affected assets."""
    auth_as(technician_user)

    asset = _create_asset(db_session, company.id, employee_user.id, serial_number="AFFECT001")
    request = _create_request(db_session, company.id, employee_user.id)

    resp = client.patch(
        f"/api/v1/requests/{request.id}/affected-assets",
        json={"asset_ids": [asset.id]},
    )

    assert resp.status_code == 200

    # Verify via requester-assets endpoint that asset is marked as affected
    resp2 = client.get(f"/api/v1/requests/{request.id}/requester-assets")
    assert resp2.status_code == 200
    data = resp2.json()["data"]
    affected = [a for a in data if a["id"] == asset.id]
    assert len(affected) == 1
    assert affected[0]["is_affected"] is True


def test_patch_invalid_asset_id_returns_404(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """PATCH with a non-existent asset ID returns 404."""
    auth_as(technician_user)

    request = _create_request(db_session, company.id, employee_user.id)
    fake_asset_id = str(ulid.new())

    resp = client.patch(
        f"/api/v1/requests/{request.id}/affected-assets",
        json={"asset_ids": [fake_asset_id]},
    )

    assert resp.status_code == 404


def test_patch_invalid_request_id_returns_404(
    client, db_session, company, technician_user, auth_as,
):
    """PATCH with a non-existent request ID returns 404."""
    auth_as(technician_user)

    fake_request_id = str(ulid.new())

    resp = client.patch(
        f"/api/v1/requests/{fake_request_id}/affected-assets",
        json={"asset_ids": []},
    )

    assert resp.status_code == 404


def test_get_requester_assets_with_is_affected(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """GET returns requester's assets, correctly marking affected ones."""
    auth_as(technician_user)

    asset1 = _create_asset(
        db_session, company.id, employee_user.id,
        serial_number="RA001", criticality=AssetCriticality.HIGH,
    )
    asset2 = _create_asset(
        db_session, company.id, employee_user.id,
        serial_number="RA002", criticality=AssetCriticality.LOW,
    )
    request = _create_request(db_session, company.id, employee_user.id)

    # Mark only asset1 as affected
    client.patch(
        f"/api/v1/requests/{request.id}/affected-assets",
        json={"asset_ids": [asset1.id]},
    )

    resp = client.get(f"/api/v1/requests/{request.id}/requester-assets")
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert len(data) == 2

    affected_map = {a["id"]: a["is_affected"] for a in data}
    assert affected_map[asset1.id] is True
    assert affected_map[asset2.id] is False


def test_get_requester_assets_no_assets(
    client, db_session, company, technician_user, employee_user, auth_as,
):
    """GET returns empty list when the requester has no assigned assets."""
    auth_as(technician_user)

    request = _create_request(db_session, company.id, employee_user.id)

    resp = client.get(f"/api/v1/requests/{request.id}/requester-assets")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
