from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class UpcomingChangeDto:
    id: str
    title: str
    change_type: str
    planned_date: Optional[datetime]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]


@dataclass
class RecentImplementedDto:
    id: str
    title: str
    change_type: str
    implemented_at: Optional[datetime]
    pir_outcome: Optional[str]


@dataclass
class ChangeDashboardDto:
    total_open: int
    pending_approval: int
    in_progress: int
    implemented: int
    scheduled_this_week: int
    status_counts: dict[str, int]
    type_counts: dict[str, int]
    upcoming_scheduled: list[UpcomingChangeDto] = field(
        default_factory=list
    )
    recently_implemented: list[RecentImplementedDto] = field(
        default_factory=list
    )
    rolled_back_90_days: int = 0


@dataclass
class ChangeDashboardQuery(Query):
    company_id: str


class ChangeDashboardQueryHandler(
    QueryHandler[ChangeDashboardQuery, ChangeDashboardDto]
):
    def __init__(
        self,
        change_repo: ChangeRequestRepositoryInterface,
        user_name_resolver: Optional[Callable] = None,
    ):
        self.change_repo = change_repo
        self.user_name_resolver = user_name_resolver

    def handle(
        self, query: ChangeDashboardQuery
    ) -> ChangeDashboardDto:
        data = self.change_repo.get_dashboard_data(query.company_id)

        status_counts: dict[str, int] = data["status_counts"]
        type_counts: dict[str, int] = data["type_counts"]

        # Compute open = all non-terminal
        terminal = {"closed", "rejected", "rolled_back"}
        total_open = sum(
            v for k, v in status_counts.items() if k not in terminal
        )

        # Resolve user names for upcoming
        upcoming_changes = data["upcoming_scheduled"]
        name_map: dict[str, str] = {}
        if self.user_name_resolver and upcoming_changes:
            user_ids = [
                c.assigned_to
                for c in upcoming_changes
                if c.assigned_to
            ]
            if user_ids:
                name_map = self.user_name_resolver(user_ids)

        upcoming_dtos = [
            UpcomingChangeDto(
                id=c.id,
                title=c.title,
                change_type=c.change_type.value,
                planned_date=c.planned_date,
                assigned_to=c.assigned_to,
                assigned_to_name=(
                    name_map.get(c.assigned_to)
                    if c.assigned_to
                    else None
                ),
            )
            for c in upcoming_changes
        ]

        recent_dtos = [
            RecentImplementedDto(
                id=r["id"],
                title=r["title"],
                change_type=r["change_type"],
                implemented_at=r["implemented_at"],
                pir_outcome=r["pir_outcome"],
            )
            for r in data["recently_implemented"]
        ]

        return ChangeDashboardDto(
            total_open=total_open,
            pending_approval=status_counts.get("pending_approval", 0),
            in_progress=status_counts.get("in_progress", 0),
            implemented=status_counts.get("implemented", 0),
            scheduled_this_week=data["scheduled_this_week"],
            status_counts=status_counts,
            type_counts=type_counts,
            upcoming_scheduled=upcoming_dtos,
            recently_implemented=recent_dtos,
            rolled_back_90_days=data["rolled_back_90_days"],
        )
