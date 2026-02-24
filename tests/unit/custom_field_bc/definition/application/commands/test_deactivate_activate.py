from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.commands.deactivate_definition import (
    DeactivateFieldDefinitionCommand,
    DeactivateFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.commands.activate_definition import (
    ActivateFieldDefinitionCommand,
    ActivateFieldDefinitionCommandHandler,
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


class TestDeactivateFieldDefinitionCommandHandler:
    def test_deactivate_success(self):
        repo = MagicMock()
        definition = _make_definition(is_active=True)
        repo.find_by_id.return_value = definition

        handler = DeactivateFieldDefinitionCommandHandler(repo=repo)
        handler.handle(
            DeactivateFieldDefinitionCommand(
                definition_id="01AAAA",
                company_id="01COMP",
            )
        )

        assert definition.is_active is False
        repo.save.assert_called_once_with(definition)

    def test_deactivate_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeactivateFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(FieldDefinitionNotFoundError):
            handler.handle(
                DeactivateFieldDefinitionCommand(
                    definition_id="01AAAA",
                    company_id="01COMP",
                )
            )
        repo.save.assert_not_called()


class TestActivateFieldDefinitionCommandHandler:
    def test_activate_success(self):
        repo = MagicMock()
        definition = _make_definition(is_active=False)
        repo.find_by_id.return_value = definition

        handler = ActivateFieldDefinitionCommandHandler(repo=repo)
        handler.handle(
            ActivateFieldDefinitionCommand(
                definition_id="01AAAA",
                company_id="01COMP",
            )
        )

        assert definition.is_active is True
        repo.save.assert_called_once_with(definition)

    def test_activate_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = ActivateFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(FieldDefinitionNotFoundError):
            handler.handle(
                ActivateFieldDefinitionCommand(
                    definition_id="01AAAA",
                    company_id="01COMP",
                )
            )
        repo.save.assert_not_called()
