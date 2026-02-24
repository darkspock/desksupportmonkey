from dataclasses import dataclass

from src.audit_bc.audit.application.dtos import GdprRequestDto
from src.audit_bc.audit.domain.exceptions import GdprRequestNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetGdprRequestQuery(Query):
    request_id: str
    company_id: str


class GetGdprRequestQueryHandler(
    QueryHandler[GetGdprRequestQuery, GdprRequestDto]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetGdprRequestQuery) -> GdprRequestDto:
        request = self.repo.find_gdpr_request_by_id(
            query.request_id, company_id=query.company_id
        )
        if request is None:
            raise GdprRequestNotFoundError(
                f"GDPR request {query.request_id} not found"
            )

        return GdprRequestDto(
            id=request.id,
            company_id=request.company_id,
            target_user_id=request.target_user_id,
            target_user_email=request.target_user_email,
            requested_by=request.requested_by,
            request_type=request.request_type.value,
            status=request.status.value,
            reason=request.reason,
            storage_key=request.storage_key,
            error_message=request.error_message,
            started_at=request.started_at,
            completed_at=request.completed_at,
            created_at=request.created_at,
        )
