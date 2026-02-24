from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.application.dtos import GdprRequestDto
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListGdprRequestsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    request_type: Optional[str] = None
    search: Optional[str] = None


class ListGdprRequestsQueryHandler(
    QueryHandler[ListGdprRequestsQuery, tuple[list[GdprRequestDto], int]]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: ListGdprRequestsQuery
    ) -> tuple[list[GdprRequestDto], int]:
        filters = {
            "page": query.page,
            "page_size": query.page_size,
            "status": query.status,
            "request_type": query.request_type,
            "search": query.search,
        }
        requests, total = self.repo.find_gdpr_requests(
            query.company_id, filters
        )
        dtos = [
            GdprRequestDto(
                id=r.id,
                company_id=r.company_id,
                target_user_id=r.target_user_id,
                target_user_email=r.target_user_email,
                requested_by=r.requested_by,
                request_type=r.request_type.value,
                status=r.status.value,
                reason=r.reason,
                storage_key=r.storage_key,
                error_message=r.error_message,
                started_at=r.started_at,
                completed_at=r.completed_at,
                created_at=r.created_at,
            )
            for r in requests
        ]
        return dtos, total
