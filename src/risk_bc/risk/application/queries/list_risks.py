from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.risk_bc.risk.domain.repository import RiskRepositoryInterface


@dataclass
class RiskListDto:
    id: str
    title: str
    category: str
    status: str
    risk_level: Optional[str]
    likelihood: Optional[int]
    impact: Optional[int]
    treatment: Optional[str]
    owner_id: Optional[str]
    owner_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ListRisksQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    category: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    treatment: Optional[str] = None
    search: Optional[str] = None


class ListRisksQueryHandler(QueryHandler[ListRisksQuery, tuple[list[RiskListDto], int]]):
    def __init__(
        self,
        risk_repo: RiskRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.risk_repo = risk_repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: ListRisksQuery) -> tuple[list[RiskListDto], int]:
        filters = {
            "page": query.page,
            "page_size": query.page_size,
            "category": query.category,
            "status": query.status,
            "risk_level": query.risk_level,
            "treatment": query.treatment,
            "search": query.search,
        }
        risks, total = self.risk_repo.find_all(query.company_id, filters)

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {r.owner_id for r in risks if r.owner_id}
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        dtos = [
            RiskListDto(
                id=r.id,
                title=r.title,
                category=r.category.value,
                status=r.status.value,
                risk_level=r.risk_level.value if r.risk_level else None,
                likelihood=r.likelihood,
                impact=r.impact,
                treatment=r.treatment.value if r.treatment else None,
                owner_id=r.owner_id,
                owner_name=name_map.get(r.owner_id, None) if r.owner_id else None,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in risks
        ]
        return dtos, total
