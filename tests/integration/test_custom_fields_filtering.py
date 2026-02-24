"""Integration tests for custom field filtering in list endpoints (F3).

Tests that assets can be filtered by custom field values using cf_ query params,
and that text search extends to custom field text values.
"""

from sqlalchemy import update

from src.company_bc.company.infrastructure.models import CompanyModel
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)


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
        label="Building",
        field_type="select",
        options=["HQ", "Branch A", "Branch B"],
    )
    defaults.update(overrides)
    defn = CustomFieldDefinition.create(**defaults)
    repo = CustomFieldDefinitionRepository(db_session)
    repo.save(defn)
    db_session.flush()
    return defn


def _create_asset(client, serial, cf_data=None):
    body = {
        "type": "laptop",
        "brand": "Dell",
        "model": "Latitude",
        "serial_number": serial,
    }
    if cf_data:
        body["custom_fields_data"] = cf_data
    resp = client.post("/api/v1/assets", json=body)
    assert resp.status_code == 201
    return resp.json()["data"]


class TestAssetCustomFieldFiltering:

    def test_filter_by_select_field(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(db_session, company)
        auth_as(technician_user)

        _create_asset(client, "CF-F1", {"building": "HQ"})
        _create_asset(client, "CF-F2", {"building": "Branch A"})
        _create_asset(client, "CF-F3", {"building": "HQ"})

        resp = client.get("/api/v1/assets", params={"cf_building": "HQ"})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        serials = {a["serial_number"] for a in data}
        assert serials == {"CF-F1", "CF-F3"}

    def test_filter_by_boolean_field(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            label="Is Leased", field_type="boolean", options=None,
        )
        auth_as(technician_user)

        _create_asset(client, "CF-B1", {"is_leased": True})
        _create_asset(client, "CF-B2", {"is_leased": False})
        _create_asset(client, "CF-B3", {"is_leased": True})

        resp = client.get("/api/v1/assets", params={"cf_is_leased": "true"})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        serials = {a["serial_number"] for a in data}
        assert serials == {"CF-B1", "CF-B3"}

    def test_text_search_includes_custom_text_fields(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(
            db_session, company,
            label="Asset Tag", field_type="text", options=None,
        )
        auth_as(technician_user)

        _create_asset(client, "CF-S1", {"asset_tag": "NYC-LAPTOP-001"})
        _create_asset(client, "CF-S2", {"asset_tag": "LON-DESKTOP-002"})

        resp = client.get("/api/v1/assets", params={"search": "NYC-LAPTOP"})

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["serial_number"] == "CF-S1"

    def test_cf_filter_combined_with_standard_filter(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(db_session, company)
        auth_as(technician_user)

        _create_asset(client, "CF-C1", {"building": "HQ"})
        _create_asset(client, "CF-C2", {"building": "HQ"})

        resp = client.get("/api/v1/assets", params={
            "cf_building": "HQ",
            "type": "desktop",
        })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 0

    def test_unknown_cf_key_ignored(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(technician_user)

        _create_asset(client, "CF-U1")

        resp = client.get("/api/v1/assets", params={"cf_nonexistent": "value"})

        assert resp.status_code == 200

    def test_no_cf_filters_returns_all(
        self, client, db_session, technician_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        _create_definition(db_session, company)
        auth_as(technician_user)

        _create_asset(client, "CF-A1", {"building": "HQ"})
        _create_asset(client, "CF-A2", {"building": "Branch A"})
        _create_asset(client, "CF-A3")

        resp = client.get("/api/v1/assets")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 3
