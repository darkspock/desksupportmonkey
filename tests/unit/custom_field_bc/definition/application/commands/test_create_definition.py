from unittest.mock import MagicMock

import pytest

from src.custom_field_bc.definition.application.commands.create_definition import (
    CreateFieldDefinitionCommand,
    CreateFieldDefinitionCommandHandler,
    MAX_FIELDS_PER_ENTITY,
)
from src.custom_field_bc.definition.domain.exceptions import (
    DuplicateFieldKeyError,
    MaxFieldsExceededError,
)


class TestCreateFieldDefinitionCommandHandler:
    def test_create_success(self):
        repo = MagicMock()
        repo.count_by_entity_type.return_value = 0
        repo.has_field_key.return_value = False

        handler = CreateFieldDefinitionCommandHandler(repo=repo)
        handler.handle(
            CreateFieldDefinitionCommand(
                definition_id="01DEF",
                company_id="01COMP",
                entity_type="asset",
                label="Cost Center",
                field_type="text",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.label == "Cost Center"
        assert saved.field_key == "cost_center"

    def test_create_max_fields_exceeded(self):
        repo = MagicMock()
        repo.count_by_entity_type.return_value = MAX_FIELDS_PER_ENTITY

        handler = CreateFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(MaxFieldsExceededError):
            handler.handle(
                CreateFieldDefinitionCommand(
                    definition_id="01DEF",
                    company_id="01COMP",
                    entity_type="asset",
                    label="New Field",
                    field_type="text",
                )
            )
        repo.save.assert_not_called()

    def test_create_duplicate_slug(self):
        repo = MagicMock()
        repo.count_by_entity_type.return_value = 5
        repo.has_field_key.return_value = True

        handler = CreateFieldDefinitionCommandHandler(repo=repo)
        with pytest.raises(DuplicateFieldKeyError):
            handler.handle(
                CreateFieldDefinitionCommand(
                    definition_id="01DEF",
                    company_id="01COMP",
                    entity_type="asset",
                    label="Cost Center",
                    field_type="text",
                )
            )
        repo.save.assert_not_called()
