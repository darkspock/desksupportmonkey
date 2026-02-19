from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid

from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)


@dataclass
class ChecklistItem:
    title: str
    description: Optional[str] = None
    is_required: bool = True

    @classmethod
    def create(
        cls,
        title: str,
        description: Optional[str] = None,
        is_required: bool = True,
    ) -> "ChecklistItem":
        if not title or not title.strip():
            raise ValueError("Checklist item title is required")
        return cls(
            title=title.strip(),
            description=description,
            is_required=is_required,
        )


@dataclass
class MaintenanceTemplate:
    id: str
    company_id: str
    name: str
    default_priority: MaintenancePriority
    description: Optional[str] = None
    recurrence_frequency: Optional[RecurrenceFrequency] = None
    recurrence_interval: int = 1
    asset_type_filter: Optional[str] = None
    checklist_items: list[ChecklistItem] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        default_priority: MaintenancePriority = MaintenancePriority.MEDIUM,
        description: Optional[str] = None,
        recurrence_frequency: Optional[RecurrenceFrequency] = None,
        recurrence_interval: int = 1,
        asset_type_filter: Optional[str] = None,
        checklist_items: Optional[list[ChecklistItem]] = None,
        id: Optional[str] = None,
    ) -> "MaintenanceTemplate":
        if not name or not name.strip():
            raise ValueError("Template name is required")
        if recurrence_interval < 1:
            raise ValueError("recurrence_interval must be >= 1")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            description=description,
            default_priority=default_priority,
            recurrence_frequency=recurrence_frequency,
            recurrence_interval=recurrence_interval,
            asset_type_filter=asset_type_filter,
            checklist_items=checklist_items or [],
            is_active=True,
        )

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_priority: Optional[MaintenancePriority] = None,
        recurrence_frequency: Optional[RecurrenceFrequency] = None,
        recurrence_interval: Optional[int] = None,
        asset_type_filter: Optional[str] = None,
        checklist_items: Optional[list[ChecklistItem]] = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValueError("Template name cannot be empty")
            self.name = name.strip()
        if description is not None:
            self.description = description
        if default_priority is not None:
            self.default_priority = default_priority
        if recurrence_frequency is not None:
            self.recurrence_frequency = recurrence_frequency
        if recurrence_interval is not None:
            if recurrence_interval < 1:
                raise ValueError("recurrence_interval must be >= 1")
            self.recurrence_interval = recurrence_interval
        if asset_type_filter is not None:
            self.asset_type_filter = asset_type_filter
        if checklist_items is not None:
            self.checklist_items = checklist_items

    def deactivate(self) -> None:
        self.is_active = False


@dataclass
class MaintenancePlan:
    id: str
    company_id: str
    template_id: str
    asset_id: str
    next_due_at: datetime
    is_active: bool = True
    last_generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        template_id: str,
        asset_id: str,
        next_due_at: datetime,
        id: Optional[str] = None,
    ) -> "MaintenancePlan":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            template_id=template_id,
            asset_id=asset_id,
            next_due_at=next_due_at,
            is_active=True,
        )

    def update_next_due(
        self,
        next_due_at: datetime,
        last_generated_at: Optional[datetime] = None,
    ) -> None:
        self.next_due_at = next_due_at
        if last_generated_at is not None:
            self.last_generated_at = last_generated_at

    def deactivate(self) -> None:
        self.is_active = False
