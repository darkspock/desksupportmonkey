from dataclasses import dataclass

from src.audit_bc.audit.application.dtos import RetentionPolicyDto
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetRetentionPolicyQuery(Query):
    company_id: str


class GetRetentionPolicyQueryHandler(
    QueryHandler[GetRetentionPolicyQuery, RetentionPolicyDto]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(self, query: GetRetentionPolicyQuery) -> RetentionPolicyDto:
        policy = self.repo.find_retention_policy(query.company_id)
        if policy is None:
            return RetentionPolicyDto(
                retention_months=36,
                updated_at=None,
                updated_by=None,
            )
        return RetentionPolicyDto(
            retention_months=policy.retention_months,
            updated_at=policy.updated_at,
            updated_by=policy.updated_by,
        )
