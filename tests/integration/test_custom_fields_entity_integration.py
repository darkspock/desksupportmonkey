"""Integration tests for custom fields entity integration (F1).

Tests that assets, requests, and incidents can be created/updated
with custom_fields_data and that responses include enriched custom_fields.
"""

from sqlalchemy import update

from src.company_bc.company.infrastructure.models import CompanyModel
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)
from datetime import datetime, timezone


def _make_enterprise(db_session, company):
    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(plan="enterprise", billing_status="active")
    )
    db_session.flush()


def _create_definition(db_session, company, **overrides):
    defaults = dict(
        company_id=company.id,
        entity_type="asset",
        label="Cost Center",
        field_type="text",
    )
    defaults.update(overrides)
    defn = CustomFieldDefinition.create(**defaults)
    repo = CustomFieldDefinitionRepository(db_session)
    repo.save(defn)
    db_session.flush()
    return defn


# ---- Assets ----


class TestAssetCustomFields:

    def test_create_asset_with_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Cost Center", field_type="text",
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": "CF-001",
            "custom_fields_data": {"cost_center": "IT-001"},
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["custom_fields"] is not None
        assert len(data["custom_fields"]) == 1
        assert data["custom_fields"][0]["key"] == "cost_center"
        assert data["custom_fields"][0]["value"] == "IT-001"
        assert data["custom_fields"][0]["label"] == "Cost Center"
        assert data["custom_fields"][0]["type"] == "text"

    def test_get_asset_includes_enriched_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Building", field_type="select",
            options=["HQ", "Branch A"],
        )
        auth_as(technician_user)

        create_resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "HP", "model": "EliteBook",
            "serial_number": "CF-002",
            "custom_fields_data": {"building": "HQ"},
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/assets/{asset_id}")

        assert resp.status_code == 200
        cf = resp.json()["data"]["custom_fields"]
        assert len(cf) == 1
        assert cf[0]["value"] == "HQ"
        assert cf[0]["options"] == ["HQ", "Branch A"]

    def test_update_asset_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Floor Number", field_type="number",
        )
        auth_as(technician_user)

        create_resp = client.post("/api/v1/assets", json={
            "type": "monitor", "brand": "LG", "model": "27UK850",
            "serial_number": "CF-003",
            "custom_fields_data": {"floor_number": 3},
        })
        asset_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/assets/{asset_id}", json={
            "custom_fields_data": {"floor_number": 5},
        })

        assert resp.status_code == 200
        cf = resp.json()["data"]["custom_fields"]
        assert cf[0]["value"] == 5

    def test_list_assets_includes_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Tag", field_type="text",
        )
        auth_as(technician_user)

        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "X1",
            "serial_number": "CF-LIST-001",
            "custom_fields_data": {"tag": "alpha"},
        })
        client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "X2",
            "serial_number": "CF-LIST-002",
            "custom_fields_data": {"tag": "beta"},
        })

        resp = client.get("/api/v1/assets")

        assert resp.status_code == 200
        items = resp.json()["data"]
        for item in items:
            assert "custom_fields" in item

    def test_create_asset_invalid_custom_field_422(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Priority", field_type="select",
            options=["Low", "Medium", "High"],
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Latitude",
            "serial_number": "CF-INVALID-001",
            "custom_fields_data": {"priority": "Critical"},  # not in options
        })

        assert resp.status_code == 422

    def test_create_asset_missing_required_field_422(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Department Code",
            field_type="text", required=True,
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Latitude",
            "serial_number": "CF-REQ-001",
            "custom_fields_data": {},  # missing required field
        })

        assert resp.status_code == 422

    def test_create_asset_without_custom_fields_ok(
        self, client, db_session, technician_user, auth_as, company
    ):
        """Assets can be created without custom_fields_data (backward compat)."""
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Optional Field", field_type="text",
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/assets", json={
            "type": "laptop", "brand": "Dell", "model": "Latitude",
            "serial_number": "CF-NODATA-001",
        })

        assert resp.status_code == 201
        cf = resp.json()["data"]["custom_fields"]
        assert len(cf) == 1
        assert cf[0]["value"] is None


# ---- Requests ----


class TestRequestCustomFields:

    def test_create_request_with_custom_fields(
        self, client, db_session, employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="request", label="Urgency Note", field_type="text",
        )
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "Network down",
            "description": "Cannot access intranet",
            "custom_fields_data": {"urgency_note": "VIP client affected"},
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["custom_fields"] is not None
        assert data["custom_fields"][0]["key"] == "urgency_note"
        assert data["custom_fields"][0]["value"] == "VIP client affected"

    def test_get_request_enriched_custom_fields(
        self, client, db_session, employee_user, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="request", label="Impact Level", field_type="select",
            options=["Low", "Medium", "High"],
        )
        auth_as(employee_user)

        create_resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "Printer broken",
            "description": "Floor 3 printer offline",
            "custom_fields_data": {"impact_level": "High"},
        })
        req_id = create_resp.json()["data"]["id"]

        # Technician fetches detail
        auth_as(technician_user)
        resp = client.get(f"/api/v1/requests/{req_id}")

        assert resp.status_code == 200
        cf = resp.json()["data"]["custom_fields"]
        assert len(cf) == 1
        assert cf[0]["value"] == "High"
        assert cf[0]["options"] == ["Low", "Medium", "High"]

    def test_create_request_invalid_custom_field_422(
        self, client, db_session, employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="request", label="Region", field_type="select",
            options=["EMEA", "AMER", "APAC"],
        )
        auth_as(employee_user)

        resp = client.post("/api/v1/requests", json={
            "type": "incident",
            "title": "Test",
            "description": "Test description",
            "custom_fields_data": {"region": "LATAM"},  # not valid
        })

        assert resp.status_code == 422


# ---- Incidents ----


class TestIncidentCustomFields:

    def test_create_incident_with_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="incident", label="Affected Systems", field_type="text",
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/incidents", json={
            "title": "Data breach detected",
            "description": "Unauthorized access to customer DB",
            "incident_type": "data_breach",
            "severity": "P1",
            "detected_at": "2026-02-20T10:00:00Z",
            "custom_fields_data": {"affected_systems": "CRM, Billing"},
        })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["custom_fields"] is not None
        assert data["custom_fields"][0]["key"] == "affected_systems"
        assert data["custom_fields"][0]["value"] == "CRM, Billing"

    def test_get_incident_enriched_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="incident", label="Response Team", field_type="multi_select",
            options=["Security", "Infrastructure", "Legal"],
        )
        auth_as(technician_user)

        create_resp = client.post("/api/v1/incidents", json={
            "title": "Ransomware detected",
            "description": "Encryption activity on file server",
            "incident_type": "malware",
            "severity": "P1",
            "detected_at": "2026-02-20T14:00:00Z",
            "custom_fields_data": {"response_team": ["Security", "Legal"]},
        })
        incident_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/v1/incidents/{incident_id}")

        assert resp.status_code == 200
        cf = resp.json()["data"]["custom_fields"]
        assert len(cf) == 1
        assert cf[0]["value"] == ["Security", "Legal"]
        assert cf[0]["options"] == ["Security", "Infrastructure", "Legal"]

    def test_update_incident_custom_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="incident", label="External Notified",
            field_type="boolean",
        )
        auth_as(technician_user)

        create_resp = client.post("/api/v1/incidents", json={
            "title": "Phishing campaign",
            "description": "Targeted phishing emails",
            "incident_type": "phishing",
            "severity": "P2",
            "detected_at": "2026-02-21T09:00:00Z",
            "custom_fields_data": {"external_notified": False},
        })
        incident_id = create_resp.json()["data"]["id"]

        resp = client.put(f"/api/v1/incidents/{incident_id}", json={
            "custom_fields_data": {"external_notified": True},
        })

        assert resp.status_code == 200
        cf = resp.json()["data"]["custom_fields"]
        assert cf[0]["value"] is True

    def test_create_incident_invalid_custom_field_422(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="incident", label="Severity Score",
            field_type="number",
        )
        auth_as(technician_user)

        resp = client.post("/api/v1/incidents", json={
            "title": "Test incident",
            "description": "Test description",
            "incident_type": "phishing",
            "severity": "P3",
            "detected_at": "2026-02-22T12:00:00Z",
            "custom_fields_data": {"severity_score": "not-a-number"},
        })

        assert resp.status_code == 422


# ---- CSV Import with custom fields ----


class TestImportAssetsWithCustomFields:

    def test_import_csv_with_custom_field_columns(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            entity_type="asset", label="Department", field_type="text",
        )
        auth_as(technician_user)

        csv_content = (
            "type,brand,model,serial_number,department\n"
            "laptop,Dell,Latitude,CF-IMP-001,Engineering\n"
            "monitor,LG,27UK850,CF-IMP-002,Design\n"
        )

        resp = client.post(
            "/api/v1/assets/import",
            files={"file": ("assets.csv", csv_content.encode(), "text/csv")},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert data["successful"] == 2

        # Verify custom fields persisted by fetching the assets
        list_resp = client.get("/api/v1/assets?type=laptop")
        laptop_items = [
            a for a in list_resp.json()["data"]
            if a["serial_number"] == "CF-IMP-001"
        ]
        assert len(laptop_items) == 1
        cf = laptop_items[0].get("custom_fields", [])
        dept_cf = [c for c in cf if c["key"] == "department"]
        assert len(dept_cf) == 1
        assert dept_cf[0]["value"] == "Engineering"
