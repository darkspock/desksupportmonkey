from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.commands.update_definition import (
    UpdateFieldDefinitionCommand,
    UpdateFieldDefinitionCommandHandler,
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


class TestUpdateFieldDefinitionCommandHandler:
    def test_update_success(self):
        repo = MagicMock()
        definition = _make_definition()
        repo.find_by_id.return_value = definition

        handler = UpdateFieldDefinitionCommandHandler(repo=repo)
        handler.handle(
            UpdateFieldDefinitionCommand(
                definition_id="01AAAA",
                company_id="01COMP",
                label="Updated Label",
                required=True,
            )
        )

        repo.save.assert_called_once_with(definition)
        assert definition.label == "Updated Label"
        assert definition.required is True

    def test_update_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UpdateFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(FieldDefinitionNotFoundError):
            handler.handle(
                UpdateFieldDefinitionCommand(
                    definition_id="01AAAA",
                    company_id="01COMP",
                    label="Updated Label",
                )
            )
        repo.save.assert_not_called()
