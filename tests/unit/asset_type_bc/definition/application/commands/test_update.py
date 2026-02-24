from unittest.mock import MagicMock

import pytest

from src.asset_type_bc.definition.application.commands.update_asset_type import (
    UpdateAssetTypeCommand,
    UpdateAssetTypeCommandHandler,
    _SENTINEL,
)
from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
    DuplicateAssetTypeCodeError,
)


def _make_definition(
    id="def1", code="laptop", name="Laptop"
):
    return AssetTypeDefinition(
        id=id,
        company_id="comp1",
        code=code,
        name=name,
        icon=None,
        is_active=True,
        sort_order=0,
    )


class TestUpdateAssetType:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = UpdateAssetTypeCommandHandler(repo=self.repo)

    def test_update_name(self):
        self.repo.find_by_id.return_value = _make_definition()
        self.repo.find_by_code.return_value = None

        self.handler.handle(
            UpdateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                name="Desktop",
            )
        )

        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        assert saved.name == "Desktop"
        assert saved.code == "desktop"

    def test_update_not_found_raises(self):
        self.repo.find_by_id.return_value = None

        with pytest.raises(AssetTypeDefinitionNotFoundError):
            self.handler.handle(
                UpdateAssetTypeCommand(
                    definition_id="def1",
                    company_id="comp1",
                    name="Desktop",
                )
            )

    def test_update_duplicate_code_raises(self):
        self.repo.find_by_id.return_value = _make_definition()
        self.repo.find_by_code.return_value = _make_definition(
            id="def2", code="desktop", name="Desktop"
        )

        with pytest.raises(DuplicateAssetTypeCodeError):
            self.handler.handle(
                UpdateAssetTypeCommand(
                    definition_id="def1",
                    company_id="comp1",
                    name="Desktop",
                )
            )

    def test_update_icon(self):
        self.repo.find_by_id.return_value = _make_definition()

        self.handler.handle(
            UpdateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                icon="new_icon",
            )
        )

        saved = self.repo.save.call_args[0][0]
        assert saved.icon == "new_icon"

    def test_update_icon_not_provided_keeps_original(self):
        defn = _make_definition()
        defn.icon = "original"
        self.repo.find_by_id.return_value = defn

        self.handler.handle(
            UpdateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                # icon defaults to _SENTINEL
            )
        )

        saved = self.repo.save.call_args[0][0]
        assert saved.icon == "original"

    def test_update_is_active(self):
        self.repo.find_by_id.return_value = _make_definition()

        self.handler.handle(
            UpdateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                is_active=False,
            )
        )

        saved = self.repo.save.call_args[0][0]
        assert saved.is_active is False
