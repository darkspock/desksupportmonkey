from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.audit_bc.audit.application.dtos import AuditEntryDto
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListAuditEntriesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    control_id: Optional[str] = None
    search: Optional[str] = None


class ListAuditEntriesQueryHandler(
    QueryHandler[ListAuditEntriesQuery, tuple[list[AuditEntryDto], int]]
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

    def handle(
        self, query: ListAuditEntriesQuery
    ) -> tuple[list[AuditEntryDto], int]:
        filters = {
            "page": query.page,
            "page_size": query.page_size,
            "date_from": query.date_from,
            "date_to": query.date_to,
            "actor_id": query.actor_id,
            "action": query.action,
            "resource_type": query.resource_type,
            "control_id": query.control_id,
            "search": query.search,
        }
        entries, total = self.repo.find_all(query.company_id, filters)

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            actor_ids = {e.actor_id for e in entries if e.actor_id}
            if actor_ids:
                name_map = self.user_name_resolver(list(actor_ids))

        # Count tags per entry
        tag_counts: dict[str, int] = {}
        for entry in entries:
            tags = self.repo.find_tags_by_entry(entry.id)
            tag_counts[entry.id] = len(tags)

        dtos = [
            AuditEntryDto(
                id=e.id,
                actor_email=e.actor_email,
                actor_name=(
                    name_map.get(e.actor_id, None)
                    if e.actor_id else None
                ),
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                http_method=e.http_method,
                response_status=e.response_status,
                ip_address=e.ip_address,
                created_at=e.created_at,
                tag_count=tag_counts.get(e.id, 0),
            )
            for e in entries
        ]
        return dtos, total
