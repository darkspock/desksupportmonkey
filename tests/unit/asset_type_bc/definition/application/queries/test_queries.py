from unittest.mock import MagicMock

import pytest

from src.asset_type_bc.definition.application.queries.list_asset_types import (
    AssetTypeDto,
    ListAssetTypesQuery,
    ListAssetTypesQueryHandler,
)
from src.asset_type_bc.definition.application.queries.get_asset_type import (
    GetAssetTypeQuery,
    GetAssetTypeQueryHandler,
)
from src.asset_type_bc.definition.domain.entities import AssetTypeDefinition
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
)


def _make_definition(code="laptop", name="Laptop", is_active=True):
    return AssetTypeDefinition(
        id="def1",
        company_id="comp1",
        code=code,
        name=name,
        icon=None,
        is_active=is_active,
        sort_order=0,
    )


class TestListAssetTypes:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = ListAssetTypesQueryHandler(repo=self.repo)

    def test_list_all(self):
        self.repo.find_all.return_value = [
            _make_definition("laptop", "Laptop"),
            _make_definition("monitor", "Monitor"),
        ]

        result = self.handler.handle(
            ListAssetTypesQuery(company_id="comp1")
        )

        assert len(result) == 2
        assert isinstance(result[0], AssetTypeDto)
        assert result[0].code == "laptop"
        self.repo.find_all.assert_called_once_with("comp1")

    def test_list_active_only(self):
        self.repo.find_active.return_value = [
            _make_definition("laptop", "Laptop"),
        ]

        result = self.handler.handle(
            ListAssetTypesQuery(
                company_id="comp1", active_only=True
            )
        )

        assert len(result) == 1
        self.repo.find_active.assert_called_once_with("comp1")


class TestGetAssetType:
    def setup_method(self):
        self.repo = MagicMock()
        self.handler = GetAssetTypeQueryHandler(repo=self.repo)

    def test_get_found(self):
        self.repo.find_by_id.return_value = _make_definition()

        result = self.handler.handle(
            GetAssetTypeQuery(
                definition_id="def1", company_id="comp1"
            )
        )

        assert isinstance(result, AssetTypeDto)
        assert result.code == "laptop"

    def test_get_not_found_raises(self):
        self.repo.find_by_id.return_value = None

        with pytest.raises(AssetTypeDefinitionNotFoundError):
            self.handler.handle(
                GetAssetTypeQuery(
                    definition_id="def1",
                    company_id="comp1",
                )
            )
