from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.domain.repository import (
    VendorDependencyRepositoryInterface,
)


@dataclass
class DependencyDto:
    id: str
    vendor_id: str
    company_id: str
    service_description: str
    business_function: str
    is_critical: bool
    notes: Optional[str]
    created_at: Optional[str]


@dataclass
class ListDependenciesQuery(Query):
    vendor_id: str
    company_id: str
    page: int = 1
    page_size: int = 20


class ListDependenciesQueryHandler(
    QueryHandler[ListDependenciesQuery, tuple[list[DependencyDto], int]],
):
    def __init__(
        self,
        dependency_repo: VendorDependencyRepositoryInterface,
    ):
        self.dependency_repo = dependency_repo

    def handle(
        self, query: ListDependenciesQuery,
    ) -> tuple[list[DependencyDto], int]:
        deps, total = self.dependency_repo.find_all_by_vendor(
            query.vendor_id,
            query.company_id,
            query.page,
            query.page_size,
        )
        dtos = [
            DependencyDto(
                id=d.id,
                vendor_id=d.vendor_id,
                company_id=d.company_id,
                service_description=d.service_description,
                business_function=d.business_function.value,
                is_critical=d.is_critical,
                notes=d.notes,
                created_at=d.created_at.isoformat() if d.created_at else None,
            )
            for d in deps
        ]
        return dtos, total
