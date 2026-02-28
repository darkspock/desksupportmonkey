"""Integration tests for /api/v1/assets/{asset_id}/relationships endpoints."""

import uuid

import pytest


def _create_asset(client, serial_number: str) -> dict:
    """Helper to create an asset and return the response data dict."""
    resp = client.post("/api/v1/assets", json={
        "type": "server",
        "brand": "Dell",
        "model": "PowerEdge R740",
        "serial_number": serial_number,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


class TestCreateCIRelationship:
    def test_create_relationship(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-SRC-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-TGT-{uuid.uuid4().hex[:8]}")

        resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "depends_on",
            "description": "Source depends on target for compute",
        })

        assert resp.status_code == 201
        data = resp.json()
        assert data["source_asset_id"] == source["id"]
        assert data["target_asset_id"] == target["id"]
        assert data["relationship_type"] == "depends_on"
        assert data["description"] == "Source depends on target for compute"
        # Enriched fields
        assert data["target_asset_name"] is not None
        assert data["target_asset_serial"] == target["serial_number"]
        assert data["target_asset_type"] == "server"
        assert data["source_asset_name"] is not None
        assert data["source_asset_serial"] == source["serial_number"]

    def test_create_self_reference_422(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset = _create_asset(client, f"REL-SELF-{uuid.uuid4().hex[:8]}")

        resp = client.post(f"/api/v1/assets/{asset['id']}/relationships", json={
            "target_asset_id": asset["id"],
            "relationship_type": "runs_on",
        })

        assert resp.status_code == 422

    def test_create_duplicate_409(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-DUP-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-DUP-T-{uuid.uuid4().hex[:8]}")

        resp1 = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "connected_to",
        })
        assert resp1.status_code == 201

        resp2 = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "connected_to",
        })

        assert resp2.status_code == 409

    def test_create_decommissioned_target_422(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-DECOM-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-DECOM-T-{uuid.uuid4().hex[:8]}")

        # Decommission the target
        client.patch(f"/api/v1/assets/{target['id']}/status", json={"status": "decommissioned"})

        resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "part_of",
        })

        assert resp.status_code == 422

    def test_create_target_not_found_404(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-NF-S-{uuid.uuid4().hex[:8]}")

        resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": "01NONEXISTENT0000000000000",
            "relationship_type": "backs_up",
        })

        assert resp.status_code == 404


class TestListCIRelationships:
    def test_list_relationships(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-LIST-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-LIST-T-{uuid.uuid4().hex[:8]}")

        client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "runs_on",
        })

        resp = client.get(f"/api/v1/assets/{source['id']}/relationships")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        rel_ids = [r["target_asset_id"] for r in data]
        assert target["id"] in rel_ids

    def test_list_empty(self, client, auth_as, technician_user):
        auth_as(technician_user)
        asset = _create_asset(client, f"REL-EMPTY-{uuid.uuid4().hex[:8]}")

        resp = client.get(f"/api/v1/assets/{asset['id']}/relationships")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_includes_enriched_fields(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-ENRICH-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-ENRICH-T-{uuid.uuid4().hex[:8]}")

        # Set criticality on target to verify enrichment
        client.patch(f"/api/v1/assets/{target['id']}/criticality", json={"criticality": "high"})

        client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "depends_on",
        })

        resp = client.get(f"/api/v1/assets/{source['id']}/relationships")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        rel = data[0]
        assert "target_asset_name" in rel
        assert "target_asset_serial" in rel
        assert "target_asset_type" in rel
        assert "target_asset_criticality" in rel
        assert rel["target_asset_criticality"] == "high"
        assert "target_asset_status" in rel
        assert "source_asset_name" in rel
        assert "source_asset_serial" in rel
        assert "source_asset_criticality" in rel


class TestUpdateCIRelationship:
    def test_update_description(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-UPD-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-UPD-T-{uuid.uuid4().hex[:8]}")

        create_resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "connected_to",
            "description": "Original description",
        })
        assert create_resp.status_code == 201
        rel_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/assets/{source['id']}/relationships/{rel_id}",
            json={"description": "Updated description"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Updated description"
        assert data["id"] == rel_id

    def test_update_not_found_404(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-UPD-NF-{uuid.uuid4().hex[:8]}")

        resp = client.patch(
            f"/api/v1/assets/{source['id']}/relationships/01NONEXISTENT0000000000000",
            json={"description": "Should fail"},
        )

        assert resp.status_code == 404


class TestDeleteCIRelationship:
    def test_delete_relationship_204(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-DEL-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-DEL-T-{uuid.uuid4().hex[:8]}")

        create_resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "part_of",
        })
        assert create_resp.status_code == 201
        rel_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/assets/{source['id']}/relationships/{rel_id}")

        assert resp.status_code == 204

        # Verify it no longer appears in the list
        list_resp = client.get(f"/api/v1/assets/{source['id']}/relationships")
        assert list_resp.status_code == 200
        remaining_ids = [r["id"] for r in list_resp.json()]
        assert rel_id not in remaining_ids

    def test_delete_not_found_404(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-DEL-NF-{uuid.uuid4().hex[:8]}")

        resp = client.delete(
            f"/api/v1/assets/{source['id']}/relationships/01NONEXISTENT0000000000000",
        )

        assert resp.status_code == 404

    def test_delete_event_recorded(self, client, auth_as, technician_user):
        auth_as(technician_user)
        source = _create_asset(client, f"REL-DEL-EVT-S-{uuid.uuid4().hex[:8]}")
        target = _create_asset(client, f"REL-DEL-EVT-T-{uuid.uuid4().hex[:8]}")

        create_resp = client.post(f"/api/v1/assets/{source['id']}/relationships", json={
            "target_asset_id": target["id"],
            "relationship_type": "backs_up",
        })
        assert create_resp.status_code == 201
        rel_id = create_resp.json()["id"]

        client.delete(f"/api/v1/assets/{source['id']}/relationships/{rel_id}")

        history = client.get(f"/api/v1/assets/{source['id']}/history")
        assert history.status_code == 200
        events = history.json()["data"]
        delete_events = [e for e in events if e["event_type"] == "ci_relationship_deleted"]
        assert len(delete_events) == 1
        assert delete_events[0]["data"]["relationship_id"] == rel_id
        assert delete_events[0]["data"]["target_asset_id"] == target["id"]
        assert delete_events[0]["data"]["relationship_type"] == "backs_up"
