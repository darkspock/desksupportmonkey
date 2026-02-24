from typing import Optional

from src.audit_bc.audit.domain.constants import sanitize_request_data
from src.audit_bc.audit.domain.entities import AuditEntry
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface


class AuditService:
    def __init__(self, repository: AuditRepositoryInterface):
        self.repository = repository

    def record(
        self,
        company_id: Optional[str],
        actor_id: Optional[str],
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        http_method: str,
        http_path: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        request_data: Optional[dict],
        response_status: int,
        changes: Optional[dict] = None,
    ) -> None:
        sanitized_data = sanitize_request_data(request_data)
        entry = AuditEntry.create(
            company_id=company_id,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            http_method=http_method,
            http_path=http_path,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=sanitized_data,
            response_status=response_status,
            changes=changes,
        )
        self.repository.save(entry)
