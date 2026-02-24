from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.risk_bc.risk.domain.exceptions import RiskNotFoundError
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class MitigationDto:
    id: str
    description: str
    status: str
    owner_id: Optional[str]
    owner_name: Optional[str]
    target_date: Optional[date]
    created_at: Optional[datetime]


@dataclass
class RiskLinkDto:
    id: str
    link_type: str
    link_id: str
    link_name: Optional[str] = None


@dataclass
class RiskHistoryDto:
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str]
    metadata: Optional[dict]
    created_at: Optional[datetime]


@dataclass
class RiskDetailDto:
    id: str
    title: str
    description: str
    category: str
    status: str
    likelihood: Optional[int]
    impact: Optional[int]
    risk_level: Optional[str]
    treatment: Optional[str]
    review_cadence: Optional[str]
    next_review_at: Optional[datetime]
    owner_id: Optional[str]
    owner_name: Optional[str]
    created_by: str
    created_by_name: Optional[str]
    mitigations: list[MitigationDto] = field(default_factory=list)
    links: list[RiskLinkDto] = field(default_factory=list)
    history: list[RiskHistoryDto] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetRiskDetailQuery(Query):
    risk_id: str
    company_id: str


class GetRiskDetailQueryHandler(
    QueryHandler[GetRiskDetailQuery, RiskDetailDto]
):
    def __init__(
        self,
        risk_repo: RiskRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.risk_repo = risk_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: GetRiskDetailQuery) -> RiskDetailDto:
        risk = self.risk_repo.find_by_id(query.risk_id, query.company_id)
        if not risk:
            raise RiskNotFoundError(query.risk_id)

        mitigations = self.risk_repo.get_mitigations(risk.id)
        links = self.risk_repo.get_links(risk.id)
        history = self.risk_repo.get_history(risk.id)

        # Resolve user names
        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids: set[str] = set()
            if risk.owner_id:
                user_ids.add(risk.owner_id)
            if risk.created_by:
                user_ids.add(risk.created_by)
            for m in mitigations:
                if m.owner_id:
                    user_ids.add(m.owner_id)
            for h in history:
                if h.actor_id:
                    user_ids.add(h.actor_id)
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        mitigation_dtos = [
            MitigationDto(
                id=m.id,
                description=m.description,
                status=m.status.value,
                owner_id=m.owner_id,
                owner_name=(
                    name_map.get(m.owner_id) if m.owner_id else None
                ),
                target_date=m.target_date,
                created_at=m.created_at,
            )
            for m in mitigations
        ]

        link_dtos = [
            RiskLinkDto(
                id=lnk.id,
                link_type=lnk.link_type.value,
                link_id=lnk.link_id,
            )
            for lnk in links
        ]

        history_dtos = [
            RiskHistoryDto(
                id=h.id,
                event_type=h.event_type.value,
                description=h.description,
                actor_id=h.actor_id,
                actor_name=name_map.get(h.actor_id),
                metadata=h.metadata,
                created_at=h.created_at,
            )
            for h in history
        ]

        return RiskDetailDto(
            id=risk.id,
            title=risk.title,
            description=risk.description,
            category=risk.category.value,
            status=risk.status.value,
            likelihood=risk.likelihood,
            impact=risk.impact,
            risk_level=risk.risk_level.value if risk.risk_level else None,
            treatment=risk.treatment.value if risk.treatment else None,
            review_cadence=(
                risk.review_cadence.value if risk.review_cadence else None
            ),
            next_review_at=risk.next_review_at,
            owner_id=risk.owner_id,
            owner_name=name_map.get(risk.owner_id) if risk.owner_id else None,
            created_by=risk.created_by,
            created_by_name=name_map.get(risk.created_by),
            mitigations=mitigation_dtos,
            links=link_dtos,
            history=history_dtos,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        )
