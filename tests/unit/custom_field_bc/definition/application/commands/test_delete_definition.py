from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.commands.delete_definition import (
    DeleteFieldDefinitionCommand,
    DeleteFieldDefinitionCommandHandler,
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


class TestDeleteFieldDefinitionCommandHandler:
    def test_delete_success(self):
        repo = MagicMock()
        definition = _make_definition()
        repo.find_by_id.return_value = definition

        handler = DeleteFieldDefinitionCommandHandler(repo=repo)
        handler.handle(
            DeleteFieldDefinitionCommand(
                definition_id="01AAAA",
                company_id="01COMP",
            )
        )

        repo.delete.assert_called_once_with("01AAAA")

    def test_delete_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeleteFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(FieldDefinitionNotFoundError):
            handler.handle(
                DeleteFieldDefinitionCommand(
                    definition_id="01AAAA",
                    company_id="01COMP",
                )
            )
        repo.delete.assert_not_called()
