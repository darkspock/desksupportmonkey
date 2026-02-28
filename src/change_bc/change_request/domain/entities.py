from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    ChangeType,
    InvalidStatusTransitionError,
    PIROutcome,
    VALID_TRANSITIONS,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotEditableError,
    RollbackPlanRequiredError,
    RollbackReasonRequiredError,
    RejectionReasonRequiredError,
)


@dataclass
class ChangeRequest:
    id: str
    company_id: str
    title: str
    description: Optional[str]
    change_type: ChangeType
    status: ChangeStatus
    business_justification: Optional[str]
    risk_assessment: Optional[str]
    rollback_plan: Optional[str]
    planned_date: Optional[datetime]
    requested_by: str
    assigned_to: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    started_at: Optional[datetime]
    implemented_at: Optional[datetime]
    implementation_notes: Optional[str]
    rolled_back_at: Optional[datetime]
    rollback_reason: Optional[str]
    closed_at: Optional[datetime]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        id: str,
        company_id: str,
        requested_by: str,
        title: str,
        change_type: ChangeType = ChangeType.STANDARD,
        planned_date: Optional[datetime] = None,
        rollback_plan: Optional[str] = None,
    ) -> "ChangeRequest":
        if not title or not title.strip():
            raise ValueError("Title is required")
        return cls(
            id=id,
            company_id=company_id,
            title=title.strip(),
            description=None,
            change_type=change_type,
            status=ChangeStatus.DRAFT,
            business_justification=None,
            risk_assessment=None,
            rollback_plan=rollback_plan,
            planned_date=planned_date,
            requested_by=requested_by,
            assigned_to=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            started_at=None,
            implemented_at=None,
            implementation_notes=None,
            rolled_back_at=None,
            rollback_reason=None,
            closed_at=None,
        )

    def _transition(self, target: ChangeStatus) -> None:
        valid_targets = VALID_TRANSITIONS.get(self.status, [])
        if target not in valid_targets:
            raise InvalidStatusTransitionError(self.status, target)
        self.status = target

    def submit(self) -> None:
        if self.change_type == ChangeType.STANDARD:
            self._transition(ChangeStatus.SCHEDULED)
        else:
            if not self.rollback_plan or not self.rollback_plan.strip():
                raise RollbackPlanRequiredError()
            self._transition(ChangeStatus.PENDING_APPROVAL)

    def approve(self, approved_by: str) -> None:
        if self.status != ChangeStatus.PENDING_APPROVAL:
            raise InvalidStatusTransitionError(self.status, ChangeStatus.SCHEDULED)
        self._transition(ChangeStatus.SCHEDULED)
        self.approved_by = approved_by
        self.approved_at = datetime.now(timezone.utc)

    def reject(self, rejected_by: str, reason: str) -> None:
        if not reason or not reason.strip():
            raise RejectionReasonRequiredError()
        self._transition(ChangeStatus.REJECTED)
        self.rejected_by = rejected_by
        self.rejected_at = datetime.now(timezone.utc)
        self.rejection_reason = reason.strip()

    def start(self) -> None:
        self._transition(ChangeStatus.IN_PROGRESS)
        self.started_at = datetime.now(timezone.utc)

    def implement(self, notes: Optional[str] = None) -> None:
        self._transition(ChangeStatus.IMPLEMENTED)
        self.implemented_at = datetime.now(timezone.utc)
        self.implementation_notes = notes

    def rollback(self, reason: str) -> None:
        if not reason or not reason.strip():
            raise RollbackReasonRequiredError()
        self._transition(ChangeStatus.ROLLED_BACK)
        self.rolled_back_at = datetime.now(timezone.utc)
        self.rollback_reason = reason.strip()

    def close(self) -> None:
        self._transition(ChangeStatus.CLOSED)
        self.closed_at = datetime.now(timezone.utc)

    def update_details(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        business_justification: Optional[str] = None,
        risk_assessment: Optional[str] = None,
        rollback_plan: Optional[str] = None,
        planned_date: Optional[datetime] = None,
    ) -> None:
        if self.status not in (ChangeStatus.DRAFT, ChangeStatus.PENDING_APPROVAL):
            raise ChangeNotEditableError(self.status.value)
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
        if description is not None:
            self.description = description
        if change_type is not None:
            self.change_type = change_type
        if business_justification is not None:
            self.business_justification = business_justification
        if risk_assessment is not None:
            self.risk_assessment = risk_assessment
        if rollback_plan is not None:
            self.rollback_plan = rollback_plan
        if planned_date is not None:
            self.planned_date = planned_date

    def assign(self, user_id: str) -> None:
        if self.status.is_terminal:
            raise InvalidStatusTransitionError(self.status, self.status)
        self.assigned_to = user_id


@dataclass
class ChangeAsset:
    id: str
    change_request_id: str
    asset_id: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls, change_request_id: str, asset_id: str
    ) -> "ChangeAsset":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            asset_id=asset_id,
        )


@dataclass
class PostImplementationReview:
    id: str
    change_request_id: str
    outcome: PIROutcome
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    created_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        change_request_id: str,
        outcome: PIROutcome,
        created_by: str,
        issues_found: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        follow_up_actions: Optional[str] = None,
    ) -> "PostImplementationReview":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            outcome=outcome,
            issues_found=issues_found,
            lessons_learned=lessons_learned,
            follow_up_actions=follow_up_actions,
            created_by=created_by,
        )


@dataclass
class ChangeEvent:
    id: str
    change_request_id: str
    event_type: ChangeEventType
    description: str
    actor_id: str
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None

    @classmethod
    def create(
        cls,
        change_request_id: str,
        event_type: ChangeEventType,
        description: str,
        actor_id: str,
        metadata: Optional[dict] = None,
    ) -> "ChangeEvent":
        return cls(
            id=str(ulid.new()),
            change_request_id=change_request_id,
            event_type=event_type,
            description=description,
            actor_id=actor_id,
            metadata=metadata,
        )
