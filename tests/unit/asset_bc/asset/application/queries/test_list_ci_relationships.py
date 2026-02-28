from unittest.mock import MagicMock

from src.asset_bc.asset.application.queries.list_ci_relationships import (
    ListCIRelationshipsQuery,
    ListCIRelationshipsQueryHandler,
)
from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.enums import CIRelationshipType


def _make_relationship(source="a1", target="a2", rel_type=CIRelationshipType.DEPENDS_ON):
    return CIRelationship.create(
        company_id="comp1",
        source_asset_id=source,
        target_asset_id=target,
        relationship_type=rel_type,
        created_by="user1",
    )


class TestListCIRelationshipsQuery:
    def test_returns_relationships(self):
        rel1 = _make_relationship(target="a2", rel_type=CIRelationshipType.DEPENDS_ON)
        rel2 = _make_relationship(target="a3", rel_type=CIRelationshipType.RUNS_ON)
        ci_repo = MagicMock()
        ci_repo.find_by_asset.return_value = [rel1, rel2]

        handler = ListCIRelationshipsQueryHandler(ci_repo=ci_repo)

        result = handler.handle(
            ListCIRelationshipsQuery(asset_id="a1", company_id="comp1")
        )

        assert result == [rel1, rel2]
        ci_repo.find_by_asset.assert_called_once_with("a1", "comp1")

    def test_empty_returns_empty(self):
        ci_repo = MagicMock()
        ci_repo.find_by_asset.return_value = []

        handler = ListCIRelationshipsQueryHandler(ci_repo=ci_repo)

        result = handler.handle(
            ListCIRelationshipsQuery(asset_id="a1", company_id="comp1")
        )

        assert result == []
        ci_repo.find_by_asset.assert_called_once_with("a1", "comp1")
