from src.asset_bc.asset.domain.entities import CIRelationship
from src.asset_bc.asset.domain.enums import CIRelationshipType


class TestCIRelationshipEntity:
    def test_create_generates_ulid(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.DEPENDS_ON,
            created_by="user1",
        )
        assert isinstance(rel.id, str)
        assert len(rel.id) > 0

    def test_create_sets_all_fields(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.RUNS_ON,
            created_by="user1",
            description="Server dependency",
        )
        assert rel.company_id == "comp1"
        assert rel.source_asset_id == "a1"
        assert rel.target_asset_id == "a2"
        assert rel.relationship_type == CIRelationshipType.RUNS_ON
        assert rel.created_by == "user1"
        assert rel.description == "Server dependency"
        assert rel.created_at is not None
        assert rel.id is not None

    def test_create_default_description_none(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.CONNECTED_TO,
            created_by="user1",
        )
        assert rel.description is None

    def test_update_description_returns_changes(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.PART_OF,
            created_by="user1",
            description="Old description",
        )
        changes = rel.update_description("New description")
        assert changes == {"description": {"old": "Old description", "new": "New description"}}
        assert rel.description == "New description"

    def test_update_description_no_change_returns_empty(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.BACKS_UP,
            created_by="user1",
            description="Same value",
        )
        changes = rel.update_description("Same value")
        assert changes == {}
        assert rel.description == "Same value"

    def test_update_description_to_none(self):
        rel = CIRelationship.create(
            company_id="comp1",
            source_asset_id="a1",
            target_asset_id="a2",
            relationship_type=CIRelationshipType.DEPENDS_ON,
            created_by="user1",
            description="Will be cleared",
        )
        changes = rel.update_description(None)
        assert changes == {"description": {"old": "Will be cleared", "new": None}}
        assert rel.description is None
