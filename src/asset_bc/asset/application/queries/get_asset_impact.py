from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from src.asset_bc.asset.domain.repository import (
    AssetRepositoryInterface,
    CIRelationshipRepositoryInterface,
)
from src.framework.application.query_bus import Query, QueryHandler


class AssetNotFoundError(Exception):
    pass


@dataclass
class ImpactAssetDto:
    id: str
    name: str
    asset_tag: Optional[str]
    criticality: Optional[str]
    depth: int
    relationship_type: str


@dataclass
class ImpactRadiusDto:
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    unclassified: int = 0
    total: int = 0


@dataclass
class AssetImpactDto:
    asset_id: str
    upstream: list[ImpactAssetDto] = field(default_factory=list)
    downstream: list[ImpactAssetDto] = field(default_factory=list)
    radius: ImpactRadiusDto = field(default_factory=ImpactRadiusDto)


@dataclass
class GetAssetImpactQuery(Query):
    asset_id: str
    company_id: str
    max_depth: int = 5


class GetAssetImpactQueryHandler(QueryHandler[GetAssetImpactQuery, AssetImpactDto]):
    def __init__(
        self,
        asset_repo: AssetRepositoryInterface,
        ci_repo: CIRelationshipRepositoryInterface,
    ):
        self.asset_repo = asset_repo
        self.ci_repo = ci_repo

    def handle(self, query: GetAssetImpactQuery) -> AssetImpactDto:
        asset = self.asset_repo.find_by_id(query.asset_id, query.company_id)
        if not asset:
            raise AssetNotFoundError(f"Asset {query.asset_id} not found")

        relationships = self.ci_repo.find_all_by_company(query.company_id)

        # Build adjacency maps
        # by_source[source_id] -> [(target_id, rel_type)] — "source depends_on target"
        by_source: dict[str, list[tuple[str, str]]] = defaultdict(list)
        # by_target[target_id] -> [(source_id, rel_type)] — "source depends_on target"
        by_target: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for rel in relationships:
            by_source[rel.source_asset_id].append(
                (rel.target_asset_id, rel.relationship_type.value)
            )
            by_target[rel.target_asset_id].append(
                (rel.source_asset_id, rel.relationship_type.value)
            )

        # BFS upstream: asset is source, follow into targets (what this asset depends on)
        upstream_raw = self._bfs(query.asset_id, by_source, query.max_depth)

        # BFS downstream: asset is target, follow into sources (what depends on this asset)
        downstream_raw = self._bfs(query.asset_id, by_target, query.max_depth)

        # Load all discovered asset details
        all_ids = {item[0] for item in upstream_raw} | {item[0] for item in downstream_raw}
        asset_map = {}
        if all_ids:
            assets = self.asset_repo.find_by_ids(list(all_ids), query.company_id)
            asset_map = {a.id: a for a in assets}

        # Build DTOs
        upstream = self._build_dtos(upstream_raw, asset_map)
        downstream = self._build_dtos(downstream_raw, asset_map)

        # Compute impact radius from downstream assets
        radius = ImpactRadiusDto()
        for item in downstream:
            crit = item.criticality or "unclassified"
            if crit == "critical":
                radius.critical += 1
            elif crit == "high":
                radius.high += 1
            elif crit == "medium":
                radius.medium += 1
            elif crit == "low":
                radius.low += 1
            else:
                radius.unclassified += 1
            radius.total += 1

        return AssetImpactDto(
            asset_id=query.asset_id,
            upstream=upstream,
            downstream=downstream,
            radius=radius,
        )

    @staticmethod
    def _bfs(
        start_id: str,
        adjacency: dict[str, list[tuple[str, str]]],
        max_depth: int,
    ) -> list[tuple[str, int, str]]:
        """BFS traversal returning [(asset_id, depth, relationship_type)]."""
        visited: set[str] = {start_id}
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])
        result: list[tuple[str, int, str]] = []

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id, rel_type in adjacency.get(current_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    result.append((neighbor_id, depth + 1, rel_type))
                    queue.append((neighbor_id, depth + 1))

        return result

    @staticmethod
    def _build_dtos(
        raw: list[tuple[str, int, str]],
        asset_map: dict,
    ) -> list[ImpactAssetDto]:
        dtos = []
        for asset_id, depth, rel_type in raw:
            asset = asset_map.get(asset_id)
            if asset:
                dtos.append(ImpactAssetDto(
                    id=asset.id,
                    name=f"{asset.brand} {asset.model}",
                    asset_tag=asset.serial_number,
                    criticality=asset.criticality.value if asset.criticality else None,
                    depth=depth,
                    relationship_type=rel_type,
                ))
        return dtos
