from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class ChangeEventDto:
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    created_at: Optional[datetime]
    metadata: Optional[dict]


@dataclass
class ChangeAssetDto:
    id: str
    asset_id: str
    asset_name: Optional[str]
    asset_tag: Optional[str]
    asset_brand: Optional[str]
    asset_model: Optional[str]
    created_at: Optional[datetime]


@dataclass
class PIRDto:
    id: str
    outcome: str
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    created_at: Optional[datetime]


@dataclass
class ChangeRequestDetailDto:
    id: str
    company_id: str
    title: str
    description: Optional[str]
    change_type: str
    status: str
    business_justification: Optional[str]
    risk_assessment: Optional[str]
    rollback_plan: Optional[str]
    planned_date: Optional[datetime]
    requested_by: str
    requested_by_name: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    approved_by: Optional[str]
    approved_by_name: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_by_name: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    started_at: Optional[datetime]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    timeline: list[ChangeEventDto]
    affected_assets: list[ChangeAssetDto] = field(default_factory=list)
    pir: Optional[PIRDto] = None


@dataclass
class GetChangeRequestDetailQuery(Query):
    change_id: str
    company_id: str


class GetChangeRequestDetailQueryHandler(
    QueryHandler[
        GetChangeRequestDetailQuery,
        Optional[ChangeRequestDetailDto],
    ]
):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        user_name_resolver: Optional[Callable] = None,
        asset_repo=None,
    ):
        self.change_repo = change_repo
        self.user_name_resolver = user_name_resolver
        self.asset_repo = asset_repo

    def handle(
        self, query: GetChangeRequestDetailQuery
    ) -> Optional[ChangeRequestDetailDto]:
        change = self.change_repo.find_by_id(
            query.change_id, query.company_id
        )
        if not change:
            return None

        events = self.change_repo.find_events(query.change_id)

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids: set[str] = {change.requested_by}
            if change.assigned_to:
                user_ids.add(change.assigned_to)
            if change.approved_by:
                user_ids.add(change.approved_by)
            if change.rejected_by:
                user_ids.add(change.rejected_by)
            for e in events:
                user_ids.add(e.actor_id)
            name_map = self.user_name_resolver(list(user_ids))

        # Resolve affected assets
        affected_assets: list[ChangeAssetDto] = []
        if self.asset_repo:
            change_assets = self.change_repo.find_assets_by_change(
                query.change_id
            )
            if change_assets:
                assets_map: dict = {}
                for ca in change_assets:
                    a = self.asset_repo.find_by_id(
                        ca.asset_id, query.company_id
                    )
                    if a:
                        assets_map[ca.asset_id] = a
                affected_assets = [
                    ChangeAssetDto(
                        id=ca.id,
                        asset_id=ca.asset_id,
                        asset_name=(
                            f"{assets_map[ca.asset_id].brand} "
                            f"{assets_map[ca.asset_id].model}"
                            if ca.asset_id in assets_map
                            else None
                        ),
                        asset_tag=(
                            assets_map[ca.asset_id].serial_number
                            if ca.asset_id in assets_map
                            else None
                        ),
                        asset_brand=(
                            assets_map[ca.asset_id].brand
                            if ca.asset_id in assets_map
                            else None
                        ),
                        asset_model=(
                            assets_map[ca.asset_id].model
                            if ca.asset_id in assets_map
                            else None
                        ),
                        created_at=ca.created_at,
                    )
                    for ca in change_assets
                ]

        # Resolve PIR
        pir_dto: Optional[PIRDto] = None
        pir = self.change_repo.find_pir_by_change(query.change_id)
        if pir:
            if (
                pir.created_by
                and pir.created_by not in name_map
                and self.user_name_resolver
            ):
                extra = self.user_name_resolver([pir.created_by])
                name_map.update(extra)
            pir_dto = PIRDto(
                id=pir.id,
                outcome=pir.outcome.value,
                issues_found=pir.issues_found,
                lessons_learned=pir.lessons_learned,
                follow_up_actions=pir.follow_up_actions,
                created_by=pir.created_by,
                created_by_name=name_map.get(pir.created_by),
                created_at=pir.created_at,
            )

        return ChangeRequestDetailDto(
            id=change.id,
            company_id=change.company_id,
            title=change.title,
            description=change.description,
            change_type=change.change_type.value,
            status=change.status.value,
            business_justification=change.business_justification,
            risk_assessment=change.risk_assessment,
            rollback_plan=change.rollback_plan,
            planned_date=change.planned_date,
            requested_by=change.requested_by,
            requested_by_name=name_map.get(change.requested_by),
            assigned_to=change.assigned_to,
            assigned_to_name=(
                name_map.get(change.assigned_to)
                if change.assigned_to
                else None
            ),
            approved_by=change.approved_by,
            approved_by_name=(
                name_map.get(change.approved_by)
                if change.approved_by
                else None
            ),
            approved_at=change.approved_at,
            rejected_by=change.rejected_by,
            rejected_by_name=(
                name_map.get(change.rejected_by)
                if change.rejected_by
                else None
            ),
            rejected_at=change.rejected_at,
            rejection_reason=change.rejection_reason,
            started_at=change.started_at,
            implemented_at=change.implemented_at,
            implementation_notes=change.implementation_notes,
            rolled_back_at=change.rolled_back_at,
            rollback_reason=change.rollback_reason,
            closed_at=change.closed_at,
            created_at=change.created_at,
            updated_at=change.updated_at,
            timeline=[
                ChangeEventDto(
                    id=e.id,
                    event_type=e.event_type.value,
                    description=e.description,
                    actor_id=e.actor_id,
                    actor_name=name_map.get(e.actor_id),
                    created_at=e.created_at,
                    metadata=e.metadata,
                )
                for e in events
            ],
            affected_assets=affected_assets,
            pir=pir_dto,
        )
