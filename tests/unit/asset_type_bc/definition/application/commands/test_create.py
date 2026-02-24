from unittest.mock import MagicMock

import pytest

from src.asset_type_bc.definition.application.commands.create_asset_type import (
    CreateAssetTypeCommand,
    CreateAssetTypeCommandHandler,
)
from src.asset_type_bc.definition.domain.exceptions import (
    DuplicateAssetTypeCodeError,
)


class TestCreateAssetType:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = CreateAssetTypeCommandHandler(repo=self.repo)

    def test_create_success(self):
        self.repo.has_code.return_value = False

        self.handler.handle(
            CreateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                name="Laptop",
            )
        )

        self.repo.save.assert_called_once()
        saved = self.repo.save.call_args[0][0]
        assert saved.id == "def1"
        assert saved.company_id == "comp1"
        assert saved.name == "Laptop"
        assert saved.code == "laptop"

    def test_create_with_icon(self):
        self.repo.has_code.return_value = False

        self.handler.handle(
            CreateAssetTypeCommand(
                definition_id="def1",
                company_id="comp1",
                name="Monitor",
                icon="monitor",
                sort_order=3,
            )
        )

        saved = self.repo.save.call_args[0][0]
        assert saved.icon == "monitor"
        assert saved.sort_order == 3

    def test_create_duplicate_code_raises(self):
        self.repo.has_code.return_value = True

        with pytest.raises(DuplicateAssetTypeCodeError):
            self.handler.handle(
                CreateAssetTypeCommand(
                    definition_id="def1",
                    company_id="comp1",
                    name="Laptop",
                )
            )

        self.repo.save.assert_not_called()
