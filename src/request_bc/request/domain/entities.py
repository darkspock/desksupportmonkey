from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.request_bc.request.domain.enums import (
    DEFAULT_PRIORITY,
    InvalidStatusTransitionError,
    RequestPriority,
    RequestStatus,
    VALID_STATUS_TRANSITIONS,
)


@dataclass
class ServiceRequest:
    id: str
    company_id: str
    created_by: str
    type: str
    title: str
    description: str
    status: RequestStatus
    priority: RequestPriority
    assigned_to: Optional[str] = None
    subtype: Optional[str] = None
    data: Optional[dict] = field(default=None)
    custom_fields_data: Optional[dict] = field(default=None)
    workflow_template_id: Optional[str] = None
    workflow_subtype_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    sla_paused_at: Optional[datetime] = None
    sla_paused_total_seconds: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        created_by: str,
        type: str,
        title: str,
        description: str,
        data: Optional[dict] = None,
        custom_fields_data: Optional[dict] = None,
        id: Optional[str] = None,
        subtype: Optional[str] = None,
        requires_approval: bool = False,
        workflow_template_id: Optional[str] = None,
        workflow_subtype_id: Optional[str] = None,
    ) -> "ServiceRequest":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not description or not description.strip():
            raise ValueError("Description is required")
        initial_status = (
            RequestStatus.PENDING_APPROVAL if requires_approval else RequestStatus.SUBMITTED
        )
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            created_by=created_by,
            type=type,
            title=title.strip(),
            description=description.strip(),
            status=initial_status,
            priority=DEFAULT_PRIORITY.get(type, RequestPriority.LOW),
            subtype=subtype,
            data=data,
            custom_fields_data=custom_fields_data or {},
            workflow_template_id=workflow_template_id,
            workflow_subtype_id=workflow_subtype_id,
        )

    def change_status(self, new_status: RequestStatus) -> None:
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(self.status, new_status)

        # SLA clock: accumulate paused time when LEAVING waiting_for_employee
        if self.status == RequestStatus.WAITING_FOR_EMPLOYEE and self.sla_paused_at:
            paused_at = self.sla_paused_at
            if paused_at.tzinfo is None:
                paused_at = paused_at.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - paused_at).total_seconds()
            self.sla_paused_total_seconds = (self.sla_paused_total_seconds or 0) + int(elapsed)
            self.sla_paused_at = None

        self.status = new_status

        # SLA clock: start pausing when ENTERING waiting_for_employee
        if new_status == RequestStatus.WAITING_FOR_EMPLOYEE:
            self.sla_paused_at = datetime.now(timezone.utc)

        if new_status in (RequestStatus.RESOLVED, RequestStatus.REJECTED):
            self.resolved_at = datetime.now(timezone.utc)

    def record_first_response(self) -> None:
        if self.first_response_at is None:
            self.first_response_at = datetime.now(timezone.utc)

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
        id: Optional[str] = None,
    ) -> "RequestComment":
        if not body or not body.strip():
            raise ValueError("Comment body is required")
        return cls(
            id=id or str(ulid.new()),
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
        id: Optional[str] = None,
    ) -> "RequestNote":
        if not body or not body.strip():
            raise ValueError("Note body is required")
        return cls(
            id=id or str(ulid.new()),
            request_id=request_id,
            author_id=author_id,
            body=body.strip(),
        )
