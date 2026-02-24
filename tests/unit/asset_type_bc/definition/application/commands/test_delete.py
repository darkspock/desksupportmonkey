from unittest.mock import MagicMock

import pytest

from src.asset_type_bc.definition.application.commands.delete_asset_type import (
    DeleteAssetTypeCommand,
    DeleteAssetTypeCommandHandler,
)
from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
    AssetTypeInUseError,
)


def _make_definition():
    return AssetTypeDefinition(
        id="def1",
        company_id="comp1",
        code="laptop",
        name="Laptop",
        icon=None,
        is_active=True,
        sort_order=0,
    )


class TestDeleteAssetType:
    def setup_method(self):
        self.repo = MagicMock()
        self.asset_repo = MagicMock()
        self.handler = DeleteAssetTypeCommandHandler(
            repo=self.repo, asset_repo=self.asset_repo
        )

    def test_delete_success(self):
        self.repo.find_by_id.return_value = _make_definition()
        self.asset_repo.find_all.return_value = ([], 0)

        self.handler.handle(
            DeleteAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
            )
        )

        self.repo.delete.assert_called_once_with("def1")

    def test_delete_not_found_raises(self):
        self.repo.find_by_id.return_value = None

        with pytest.raises(AssetTypeDefinitionNotFoundError):
            self.handler.handle(
                DeleteAssetTypeCommand(
                    definition_id="def1",
                    company_id="comp1",
                )
            )

        self.repo.delete.assert_not_called()

    def test_delete_in_use_raises(self):
        self.repo.find_by_id.return_value = _make_definition()
        self.asset_repo.find_all.return_value = ([MagicMock()], 1)

        with pytest.raises(AssetTypeInUseError):
            self.handler.handle(
                DeleteAssetTypeCommand(
                    definition_id="def1",
                    company_id="comp1",
                )
            )

        self.repo.delete.assert_not_called()
