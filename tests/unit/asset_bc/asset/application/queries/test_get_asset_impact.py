from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.asset_bc.asset.application.queries.get_asset_impact import (
    AssetImpactDto,
    AssetNotFoundError,
    GetAssetImpactQuery,
    GetAssetImpactQueryHandler,
    ImpactRadiusDto,
)
from src.asset_bc.asset.domain.entities import Asset, CIRelationship
from src.asset_bc.asset.domain.enums import AssetCriticality, CIRelationshipType


COMPANY_ID = "comp1"


def _make_asset(
    asset_id: str,
    brand: str = "Dell",
    model: str = "Latitude",
    serial_number: str | None = None,
    criticality: AssetCriticality | None = None,
) -> Asset:
    asset = Asset.create(
        company_id=COMPANY_ID,
        type="laptop",
        brand=brand,
        model=model,
        serial_number=serial_number or f"SN-{asset_id}",
        id=asset_id,
    )
    asset.criticality = criticality
    return asset


def _make_relationship(
    source: str,
    target: str,
    rel_type: CIRelationshipType = CIRelationshipType.DEPENDS_ON,
) -> CIRelationship:
    return CIRelationship.create(
        company_id=COMPANY_ID,
        source_asset_id=source,
        target_asset_id=target,
        relationship_type=rel_type,
        created_by="user1",
    )


def _build_handler(
    find_by_id_return=None,
    find_all_by_company_return=None,
    find_by_ids_return=None,
):
    """Build handler with pre-configured mocked repositories."""
    asset_repo = MagicMock()
    ci_repo = MagicMock()

    asset_repo.find_by_id.return_value = find_by_id_return
    ci_repo.find_all_by_company.return_value = find_all_by_company_return or []
    asset_repo.find_by_ids.return_value = find_by_ids_return or []

    handler = GetAssetImpactQueryHandler(
        asset_repo=asset_repo,
        ci_repo=ci_repo,
    )
    return handler, asset_repo, ci_repo


# ── Test 1: No relationships ────────────────────────────────────────────


def test_no_relationships_returns_empty_impact():
    root = _make_asset("root")
    handler, asset_repo, ci_repo = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=[],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID)
    )

    assert result.asset_id == "root"
    assert result.upstream == []
    assert result.downstream == []
    assert result.radius == ImpactRadiusDto(
        critical=0, high=0, medium=0, low=0, unclassified=0, total=0,
    )
    asset_repo.find_by_id.assert_called_once_with("root", COMPANY_ID)
    ci_repo.find_all_by_company.assert_called_once_with(COMPANY_ID)
    asset_repo.find_by_ids.assert_not_called()


# ── Test 2: Flat dependencies (depth 1 only) ────────────────────────────


def test_flat_dependencies_correct_upstream_downstream():
    """
    root --depends_on--> upstream1    (root is source, upstream1 is target)
    downstream1 --depends_on--> root  (downstream1 is source, root is target)
    """
    root = _make_asset("root")
    upstream1 = _make_asset("up1", brand="HP", model="ProBook", criticality=AssetCriticality.HIGH)
    downstream1 = _make_asset("down1", brand="Lenovo", model="ThinkPad", criticality=AssetCriticality.MEDIUM)

    relationships = [
        _make_relationship("root", "up1", CIRelationshipType.DEPENDS_ON),
        _make_relationship("down1", "root", CIRelationshipType.DEPENDS_ON),
    ]

    handler, asset_repo, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[upstream1, downstream1],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID)
    )

    assert len(result.upstream) == 1
    assert result.upstream[0].id == "up1"
    assert result.upstream[0].name == "HP ProBook"
    assert result.upstream[0].depth == 1
    assert result.upstream[0].relationship_type == "depends_on"

    assert len(result.downstream) == 1
    assert result.downstream[0].id == "down1"
    assert result.downstream[0].name == "Lenovo ThinkPad"
    assert result.downstream[0].depth == 1


# ── Test 3: Nested dependencies (depth 2-3) ─────────────────────────────


def test_nested_dependencies_bfs_multiple_levels():
    """
    Upstream chain:  root -> A -> B -> C   (root depends_on A, A depends_on B, etc.)
    Each node should appear at its correct depth.
    """
    root = _make_asset("root")
    a = _make_asset("A", brand="HP", model="Server")
    b = _make_asset("B", brand="Cisco", model="Switch")
    c = _make_asset("C", brand="APC", model="UPS")

    relationships = [
        _make_relationship("root", "A", CIRelationshipType.DEPENDS_ON),
        _make_relationship("A", "B", CIRelationshipType.DEPENDS_ON),
        _make_relationship("B", "C", CIRelationshipType.DEPENDS_ON),
    ]

    handler, asset_repo, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[a, b, c],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID)
    )

    upstream_map = {dto.id: dto for dto in result.upstream}
    assert len(upstream_map) == 3
    assert upstream_map["A"].depth == 1
    assert upstream_map["B"].depth == 2
    assert upstream_map["C"].depth == 3

    # No downstream since nobody depends on root
    assert result.downstream == []


# ── Test 4: Cycle detection ──────────────────────────────────────────────


def test_cycle_detection_no_infinite_loop():
    """
    A -> B -> C -> A  (circular dependency)
    Starting from A, BFS should visit B and C exactly once.
    """
    root = _make_asset("A")
    b = _make_asset("B", brand="HP", model="Server")
    c = _make_asset("C", brand="Cisco", model="Router")

    relationships = [
        _make_relationship("A", "B", CIRelationshipType.DEPENDS_ON),
        _make_relationship("B", "C", CIRelationshipType.DEPENDS_ON),
        _make_relationship("C", "A", CIRelationshipType.DEPENDS_ON),
    ]

    handler, _, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[b, c],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="A", company_id=COMPANY_ID, max_depth=10)
    )

    upstream_ids = [dto.id for dto in result.upstream]
    assert sorted(upstream_ids) == ["B", "C"]
    # Each node appears exactly once
    assert len(upstream_ids) == len(set(upstream_ids))


# ── Test 5: Max depth limit ─────────────────────────────────────────────


def test_max_depth_limit_excludes_beyond():
    """
    root -> A -> B -> C -> D
    With max_depth=2 we should only see A (depth 1) and B (depth 2).
    """
    root = _make_asset("root")
    a = _make_asset("A", brand="HP", model="Server")
    b = _make_asset("B", brand="Cisco", model="Switch")
    c = _make_asset("C", brand="APC", model="UPS")
    d = _make_asset("D", brand="Dell", model="Storage")

    relationships = [
        _make_relationship("root", "A", CIRelationshipType.DEPENDS_ON),
        _make_relationship("A", "B", CIRelationshipType.DEPENDS_ON),
        _make_relationship("B", "C", CIRelationshipType.DEPENDS_ON),
        _make_relationship("C", "D", CIRelationshipType.DEPENDS_ON),
    ]

    handler, _, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[a, b],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID, max_depth=2)
    )

    upstream_ids = {dto.id for dto in result.upstream}
    assert upstream_ids == {"A", "B"}
    assert all(dto.depth <= 2 for dto in result.upstream)


# ── Test 6: Mixed relationship types ────────────────────────────────────


def test_mixed_relationship_types_traversed_correctly():
    """
    root --depends_on--> A
    root --runs_on--> B
    C --connected_to--> root   (downstream)
    """
    root = _make_asset("root")
    a = _make_asset("A", brand="HP", model="Server")
    b = _make_asset("B", brand="VMware", model="ESXi")
    c = _make_asset("C", brand="Cisco", model="Firewall")

    relationships = [
        _make_relationship("root", "A", CIRelationshipType.DEPENDS_ON),
        _make_relationship("root", "B", CIRelationshipType.RUNS_ON),
        _make_relationship("C", "root", CIRelationshipType.CONNECTED_TO),
    ]

    handler, _, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[a, b, c],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID)
    )

    upstream_map = {dto.id: dto for dto in result.upstream}
    assert len(upstream_map) == 2
    assert upstream_map["A"].relationship_type == "depends_on"
    assert upstream_map["B"].relationship_type == "runs_on"

    assert len(result.downstream) == 1
    assert result.downstream[0].id == "C"
    assert result.downstream[0].relationship_type == "connected_to"


# ── Test 7: Asset not found raises ───────────────────────────────────────


def test_asset_not_found_raises_error():
    handler, _, _ = _build_handler(find_by_id_return=None)

    with pytest.raises(AssetNotFoundError, match="Asset bad-id not found"):
        handler.handle(
            GetAssetImpactQuery(asset_id="bad-id", company_id=COMPANY_ID)
        )


# ── Test 8: Impact radius calculation ───────────────────────────────────


def test_impact_radius_groups_downstream_by_criticality():
    """
    Multiple downstream assets with varying criticalities; None maps to unclassified.
    """
    root = _make_asset("root")

    d_critical = _make_asset("d1", criticality=AssetCriticality.CRITICAL)
    d_high = _make_asset("d2", criticality=AssetCriticality.HIGH)
    d_medium = _make_asset("d3", criticality=AssetCriticality.MEDIUM)
    d_low = _make_asset("d4", criticality=AssetCriticality.LOW)
    d_none = _make_asset("d5", criticality=None)
    d_critical2 = _make_asset("d6", criticality=AssetCriticality.CRITICAL)

    # All downstream: each depends on root
    relationships = [
        _make_relationship("d1", "root", CIRelationshipType.DEPENDS_ON),
        _make_relationship("d2", "root", CIRelationshipType.DEPENDS_ON),
        _make_relationship("d3", "root", CIRelationshipType.DEPENDS_ON),
        _make_relationship("d4", "root", CIRelationshipType.DEPENDS_ON),
        _make_relationship("d5", "root", CIRelationshipType.DEPENDS_ON),
        _make_relationship("d6", "root", CIRelationshipType.DEPENDS_ON),
    ]

    handler, _, _ = _build_handler(
        find_by_id_return=root,
        find_all_by_company_return=relationships,
        find_by_ids_return=[d_critical, d_high, d_medium, d_low, d_none, d_critical2],
    )

    result = handler.handle(
        GetAssetImpactQuery(asset_id="root", company_id=COMPANY_ID)
    )

    assert result.radius.critical == 2
    assert result.radius.high == 1
    assert result.radius.medium == 1
    assert result.radius.low == 1
    assert result.radius.unclassified == 1
    assert result.radius.total == 6

    # No upstream since root is not source of any relationship
    assert result.upstream == []
