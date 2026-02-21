from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

import ulid

from src.maintenance_bc.maintenance_record.domain.enums import (
    InvalidMaintenanceStatusTransitionError,
    MaintenancePriority,
    MaintenanceStatus,
    VALID_TRANSITIONS,
)


@dataclass
class MaintenanceRecord:
    id: str
    company_id: str
    asset_id: str
    status: MaintenanceStatus
    priority: MaintenancePriority
    title: str
    description: Optional[str] = None
    technician_id: Optional[str] = None
    template_id: Optional[str] = None
    plan_id: Optional[str] = None
    checklist_items: list[str] = field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    actual_findings: Optional[str] = None
    cancellation_reason: Optional[str] = None
    skip_reason: Optional[str] = None
    reminder_48h_sent: bool = False
    overdue_alert_sent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Read-model projections (populated by list queries with JOINs)
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        asset_id: str,
        title: str,
        priority: MaintenancePriority = MaintenancePriority.MEDIUM,
        description: Optional[str] = None,
        technician_id: Optional[str] = None,
        template_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        checklist_items: Optional[list[str]] = None,
        scheduled_at: Optional[datetime] = None,
        id: Optional[str] = None,
    ) -> "MaintenanceRecord":
        if not title or not title.strip():
            raise ValueError("Maintenance title is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            asset_id=asset_id,
            status=MaintenanceStatus.SCHEDULED,
            priority=priority,
            title=title.strip(),
            description=description,
            technician_id=technician_id,
            template_id=template_id,
            plan_id=plan_id,
            checklist_items=checklist_items or [],
            scheduled_at=scheduled_at,
        )

    def _transition(self, target: MaintenanceStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            raise InvalidMaintenanceStatusTransitionError(
                self.status, target,
            )
        self.status = target

    def assign(self, technician_id: str) -> None:
        if not technician_id:
            raise ValueError("technician_id is required")
        if self.status.is_terminal:
            raise ValueError(
                "Cannot assign technician to terminal maintenance record"
            )
        self.technician_id = technician_id

    def update_scheduled(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[MaintenancePriority] = None,
        checklist_items: Optional[list[str]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> None:
        if self.status != MaintenanceStatus.SCHEDULED:
            raise ValueError("Only SCHEDULED records can be updated")
        if title is not None:
            if not title.strip():
                raise ValueError("title cannot be empty")
            self.title = title.strip()
        if description is not None:
            self.description = description
        if priority is not None:
            self.priority = priority
        if checklist_items is not None:
            self.checklist_items = checklist_items
        if scheduled_at is not None:
            self.scheduled_at = scheduled_at

    def start(self) -> None:
        if not self.technician_id:
            raise ValueError("Cannot start maintenance without technician assignment")
        self._transition(MaintenanceStatus.IN_PROGRESS)
        self.started_at = datetime.now(UTC)

    def complete(
        self,
        completion_notes: Optional[str] = None,
        actual_findings: Optional[str] = None,
    ) -> None:
        self._transition(MaintenanceStatus.COMPLETED)
        self.completed_at = datetime.now(UTC)
        self.completion_notes = completion_notes
        self.actual_findings = actual_findings

    def cancel(self, reason: str) -> None:
        if not reason or not reason.strip():
            raise ValueError("Cancellation reason is required")
        self._transition(MaintenanceStatus.CANCELLED)
        self.cancellation_reason = reason.strip()

    def skip(self, reason: str) -> None:
        if not reason or not reason.strip():
            raise ValueError("Skip reason is required")
        self._transition(MaintenanceStatus.SKIPPED)
        self.skip_reason = reason.strip()

    def mark_reminder_sent(self) -> None:
        self.reminder_48h_sent = True

    def mark_overdue_alert_sent(self) -> None:
        self.overdue_alert_sent = True
