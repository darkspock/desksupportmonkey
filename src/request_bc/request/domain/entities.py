from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.request_bc.request.domain.enums import (
    DEFAULT_PRIORITY,
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    RequestType,
    VALID_STATUS_TRANSITIONS,
)


@dataclass
class ServiceRequest:
    id: str
    company_id: str
    created_by: str
    type: RequestType
    title: str
    description: str
    status: RequestStatus
    priority: RequestPriority
    assigned_to: Optional[str] = None
    data: Optional[dict] = field(default=None)
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        created_by: str,
        type: RequestType,
        title: str,
        description: str,
        data: Optional[dict] = None,
    ) -> "ServiceRequest":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not description or not description.strip():
            raise ValueError("Description is required")
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            created_by=created_by,
            type=type,
            title=title.strip(),
            description=description.strip(),
            status=RequestStatus.SUBMITTED,
            priority=DEFAULT_PRIORITY[type],
            data=data,
        )

    def change_status(self, new_status: RequestStatus) -> None:
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(self.status, new_status)
        self.status = new_status
        if new_status in (RequestStatus.RESOLVED, RequestStatus.REJECTED):
            self.resolved_at = datetime.now(timezone.utc)

    def change_priority(self, new_priority: RequestPriority) -> None:
        self.priority = new_priority

    def assign(self, user_id: str) -> None:
        self.assigned_to = user_id


@dataclass
class RequestEvent:
    id: str
    request_id: str
    event_type: str
    data: dict
    performed_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        request_id: str,
        event_type: str,
        data: dict,
        performed_by: str,
    ) -> "RequestEvent":
        return cls(
            id=str(ulid.new()),
            request_id=request_id,
            event_type=event_type,
            data=data,
            performed_by=performed_by,
        )


@dataclass
class RequestComment:
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        request_id: str,
        author_id: str,
        body: str,
    ) -> "RequestComment":
        if not body or not body.strip():
            raise ValueError("Comment body is required")
        return cls(
            id=str(ulid.new()),
            request_id=request_id,
            author_id=author_id,
            body=body.strip(),
        )


@dataclass
class RequestNote:
    id: str
    request_id: str
    author_id: str
    body: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        request_id: str,
        author_id: str,
        body: str,
    ) -> "RequestNote":
        if not body or not body.strip():
            raise ValueError("Note body is required")
        return cls(
            id=str(ulid.new()),
            request_id=request_id,
            author_id=author_id,
            body=body.strip(),
        )
