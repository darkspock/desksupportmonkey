from unittest.mock import MagicMock

from src.custom_field_bc.definition.application.commands.reorder_definitions import (
    ReorderFieldDefinitionsCommand,
    ReorderFieldDefinitionsCommandHandler,
)


class TestReorderFieldDefinitionsCommandHandler:
    def test_reorder_success(self):
        repo = MagicMock()

        handler = ReorderFieldDefinitionsCommandHandler(repo=repo)
        handler.handle(
            ReorderFieldDefinitionsCommand(
                company_id="01COMP",
                entity_type="asset",
                field_ids=["01AA", "01BB", "01CC"],
            )
        )

        expected_updates = [("01AA", 0), ("01BB", 1), ("01CC", 2)]
        repo.bulk_update_sort_order.assert_called_once_with(expected_updates)
