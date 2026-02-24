from dataclasses import dataclass
from typing import Callable, Optional

from src.audit_bc.audit.application.dtos import (
    AuditEntryDetailDto,
    AuditTagDto,
)
from src.audit_bc.audit.domain.exceptions import AuditEntryNotFoundError
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetAuditEntryQuery(Query):
    entry_id: str
    company_id: str


class GetAuditEntryQueryHandler(
    QueryHandler[GetAuditEntryQuery, AuditEntryDetailDto]
):
    def __init__(
        self,
        repo: AuditRepositoryInterface,
        user_name_resolver: Optional[
            Callable[[list[str]], dict[str, str]]
        ] = None,
    ):
        self.repo = repo
        self.user_name_resolver = user_name_resolver

    def handle(self, query: GetAuditEntryQuery) -> AuditEntryDetailDto:
        entry = self.repo.find_by_id(
            query.entry_id, company_id=query.company_id
        )
        if entry is None:
            raise AuditEntryNotFoundError(
                f"Audit entry {query.entry_id} not found"
            )

        # Resolve actor name
        actor_name: Optional[str] = None
        if entry.actor_id and self.user_name_resolver:
            name_map = self.user_name_resolver([entry.actor_id])
            actor_name = name_map.get(entry.actor_id)

        # Resolve tags with control info
        tags = self.repo.find_tags_by_entry(entry.id)
        tag_dtos: list[AuditTagDto] = []
        for tag in tags:
            control = self.repo.find_control_by_id(tag.control_id)
            if control:
                tag_dtos.append(
                    AuditTagDto(
                        id=tag.id,
                        control_id=tag.control_id,
                        control_code=control.code,
                        control_name=control.name,
                        framework=control.framework,
                        tagged_by=tag.tagged_by,
                        tagged_at=tag.tagged_at,
                    )
                )

        return AuditEntryDetailDto(
            id=entry.id,
            company_id=entry.company_id,
            actor_id=entry.actor_id,
            actor_email=entry.actor_email,
            actor_name=actor_name,
            action=entry.action,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            http_method=entry.http_method,
            http_path=entry.http_path,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            request_data=entry.request_data,
            response_status=entry.response_status,
            changes=entry.changes,
            hash=entry.hash,
            created_at=entry.created_at,
            tags=tag_dtos,
        )
