"""Integration tests for custom field definition CRUD endpoints."""
from sqlalchemy import update

from src.company_bc.company.infrastructure.models import CompanyModel
from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)
from datetime import datetime, timezone


def _make_enterprise(db_session, company):
    """Set company to Enterprise plan."""
    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(plan="enterprise", billing_status="active")
    )
    db_session.flush()


def _expire_trial(db_session, company):
    """Expire company trial so plan gate enforces the free plan."""
    db_session.execute(
        update(CompanyModel)
        .where(CompanyModel.id == company.id)
        .values(trial_ends_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    )
    db_session.flush()


def _create_definition(db_session, company, **overrides):
    """Helper to create a definition directly in the DB."""
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


BASE_URL = "/api/v1/custom-fields/definitions"


class TestCreateDefinition:

    def test_create_definition_201(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Cost Center",
                "field_type": "text",
                "required": True,
                "visible_to_employees": False,
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["label"] == "Cost Center"
        assert data["field_key"] == "cost_center"
        assert data["field_type"] == "text"
        assert data["required"] is True
        assert data["visible_to_employees"] is False
        assert data["is_active"] is True

    def test_create_select_with_options(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Building",
                "field_type": "select",
                "options": ["HQ", "Branch A", "Branch B"],
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["options"] == ["HQ", "Branch A", "Branch B"]

    def test_create_non_enterprise_returns_402(
        self, client, db_session, admin_user, auth_as, company
    ):
        _expire_trial(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Test Field",
                "field_type": "text",
            },
        )

        assert resp.status_code == 402

    def test_create_max_fields_exceeded_422(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        # Create 20 definitions directly
        for i in range(20):
            _create_definition(
                db_session, company, label=f"Field {i}", entity_type="asset"
            )

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Field 21",
                "field_type": "text",
            },
        )

        assert resp.status_code == 422
        assert "Maximum" in resp.json()["detail"]

    def test_create_duplicate_slug_409(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        _create_definition(
            db_session, company, label="Cost Center", entity_type="asset"
        )

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Cost Center",
                "field_type": "number",
            },
        )

        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_create_select_without_options_422(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(
            BASE_URL,
            json={
                "entity_type": "asset",
                "label": "Category",
                "field_type": "select",
            },
        )

        assert resp.status_code == 422


class TestListDefinitions:

    def test_list_by_entity_type(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        _create_definition(
            db_session, company, label="Field A", entity_type="asset", sort_order=1
        )
        _create_definition(
            db_session, company, label="Field B", entity_type="asset", sort_order=0
        )
        _create_definition(
            db_session, company, label="Field C", entity_type="request"
        )

        resp = client.get(f"{BASE_URL}?entity_type=asset")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2
        # Sorted by sort_order
        assert data[0]["label"] == "Field B"
        assert data[1]["label"] == "Field A"


class TestGetDefinition:

    def test_get_single(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        defn = _create_definition(db_session, company)

        resp = client.get(f"{BASE_URL}/{defn.id}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == defn.id
        assert data["label"] == "Cost Center"

    def test_get_not_found_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.get(f"{BASE_URL}/nonexistent_id_000000000")

        assert resp.status_code == 404


class TestUpdateDefinition:

    def test_update_200(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        defn = _create_definition(db_session, company)

        resp = client.put(
            f"{BASE_URL}/{defn.id}",
            json={"label": "Updated Label", "required": True},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["label"] == "Updated Label"
        assert data["required"] is True

    def test_update_not_found_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.put(
            f"{BASE_URL}/nonexistent_id_000000000",
            json={"label": "Test"},
        )

        assert resp.status_code == 404


class TestDeleteDefinition:

    def test_delete_204(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        defn = _create_definition(db_session, company)

        resp = client.delete(f"{BASE_URL}/{defn.id}")

        assert resp.status_code == 204

        # Verify it's gone
        resp2 = client.get(f"{BASE_URL}/{defn.id}")
        assert resp2.status_code == 404

    def test_delete_not_found_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.delete(f"{BASE_URL}/nonexistent_id_000000000")

        assert resp.status_code == 404


class TestDeactivateActivate:

    def test_deactivate_200(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        defn = _create_definition(db_session, company)

        resp = client.post(f"{BASE_URL}/{defn.id}/deactivate")

        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is False

    def test_activate_200(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        defn = _create_definition(db_session, company)
        defn.deactivate()
        CustomFieldDefinitionRepository(db_session).save(defn)
        db_session.flush()

        resp = client.post(f"{BASE_URL}/{defn.id}/activate")

        assert resp.status_code == 200
        assert resp.json()["data"]["is_active"] is True

    def test_deactivate_not_found_404(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        resp = client.post(f"{BASE_URL}/nonexistent_id_000000000/deactivate")

        assert resp.status_code == 404


class TestReorder:

    def test_reorder_200(
        self, client, db_session, admin_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(admin_user)

        d1 = _create_definition(
            db_session, company, label="Field A", sort_order=0
        )
        d2 = _create_definition(
            db_session, company, label="Field B", sort_order=1
        )

        resp = client.put(
            f"{BASE_URL}/reorder",
            json={
                "entity_type": "asset",
                "field_ids": [d2.id, d1.id],
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        # After reorder, d2 should be first (sort_order=0), d1 second (sort_order=1)
        assert data[0]["id"] == d2.id
        assert data[0]["sort_order"] == 0
        assert data[1]["id"] == d1.id
        assert data[1]["sort_order"] == 1


class TestRoleGating:

    def test_employee_cannot_access_403(
        self, client, db_session, employee_user, auth_as, company
    ):
        _make_enterprise(db_session, company)
        auth_as(employee_user)

        resp = client.get(f"{BASE_URL}?entity_type=asset")

        assert resp.status_code == 403
