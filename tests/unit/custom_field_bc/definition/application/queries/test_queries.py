from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.queries.list_definitions import (
    FieldDefinitionDto,
    ListFieldDefinitionsQuery,
    ListFieldDefinitionsQueryHandler,
)
from src.custom_field_bc.definition.application.queries.get_definition import (
    GetFieldDefinitionQuery,
    GetFieldDefinitionQueryHandler,
)
from src.custom_field_bc.definition.domain.exceptions import FieldDefinitionNotFoundError


def _make_definition(**overrides):
    from src.custom_field_bc.definition.domain.entities import CustomFieldDefinition
    defaults = dict(
        id="01AAAA",
        company_id="01COMP",
        entity_type="asset",
        field_key="cost_center",
        label="Cost Center",
        description=None,
        field_type="text",
        options=None,
        required=False,
        sort_order=0,
        is_active=True,
        visible_to_employees=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(overrides)
    return CustomFieldDefinition(**defaults)


class TestListFieldDefinitionsQueryHandler:
    def test_list_returns_sorted(self):
        repo = MagicMock()
        definition_a = _make_definition(id="01AAAA", label="Cost Center", sort_order=0)
        definition_b = _make_definition(id="01BBBB", label="Department", sort_order=1)
        repo.find_by_entity_type.return_value = [definition_a, definition_b]

        handler = ListFieldDefinitionsQueryHandler(repo=repo)
        result = handler.handle(
            ListFieldDefinitionsQuery(company_id="01COMP", entity_type="asset")
        )

        assert len(result) == 2
        assert isinstance(result[0], FieldDefinitionDto)
        assert result[0].id == "01AAAA"
        assert result[0].label == "Cost Center"
        assert result[1].id == "01BBBB"
        assert result[1].label == "Department"

    def test_list_returns_empty(self):
        repo = MagicMock()
        repo.find_by_entity_type.return_value = []

        handler = ListFieldDefinitionsQueryHandler(repo=repo)
        result = handler.handle(
            ListFieldDefinitionsQuery(company_id="01COMP", entity_type="asset")
        )

        assert result == []


class TestGetFieldDefinitionQueryHandler:
    def test_get_success(self):
        repo = MagicMock()
        definition = _make_definition()
        repo.find_by_id.return_value = definition

        handler = GetFieldDefinitionQueryHandler(repo=repo)
        result = handler.handle(
            GetFieldDefinitionQuery(definition_id="01AAAA", company_id="01COMP")
        )

        assert isinstance(result, FieldDefinitionDto)
        assert result.id == "01AAAA"
        assert result.label == "Cost Center"
        assert result.field_key == "cost_center"
        assert result.field_type == "text"

    def test_get_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = GetFieldDefinitionQueryHandler(repo=repo)
        with pytest.raises(FieldDefinitionNotFoundError):
            handler.handle(
                GetFieldDefinitionQuery(definition_id="01AAAA", company_id="01COMP")
            )
