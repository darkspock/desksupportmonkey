from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import ulid


@dataclass
class ChecklistItemDefinition:
    id: str
    template_id: str
    title: str
    description: Optional[str]
    assignee_role: Optional[str]
    sort_order: int
    is_required: bool

    @classmethod
    def create(
        cls,
        template_id: str,
        title: str,
        description: Optional[str] = None,
        assignee_role: Optional[str] = None,
        sort_order: int = 0,
        is_required: bool = True,
        id: Optional[str] = None,
    ) -> "ChecklistItemDefinition":
        if not title or not title.strip():
            raise ValueError("Checklist item title is required")
        return cls(
            id=id or str(ulid.new()),
            template_id=template_id,
            title=title.strip(),
            description=description.strip() if description else None,
            assignee_role=assignee_role,
            sort_order=sort_order,
            is_required=is_required,
        )


@dataclass
class WorkflowSubtype:
    id: str
    template_id: str
    name: str
    description: Optional[str]
    sort_order: int
    is_active: bool = True

    @classmethod
    def create(
        cls,
        template_id: str,
        name: str,
        description: Optional[str] = None,
        sort_order: int = 0,
        id: Optional[str] = None,
        is_active: bool = True,
    ) -> "WorkflowSubtype":
        if not name or not name.strip():
            raise ValueError("Subtype name is required")
        return cls(
            id=id or str(ulid.new()),
            template_id=template_id,
            name=name.strip(),
            description=description.strip() if description else None,
            sort_order=sort_order,
            is_active=is_active,
        )


@dataclass
class WorkflowTemplate:
    id: str
    company_id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: bool
    require_all_complete: bool
    sort_order: int
    subtypes: list[WorkflowSubtype] = field(default_factory=list)
    checklist_items: list[ChecklistItemDefinition] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        require_all_complete: bool = False,
        sort_order: int = 0,
        id: Optional[str] = None,
    ) -> "WorkflowTemplate":
        if not name or not name.strip():
            raise ValueError("Template name is required")
        now = datetime.now(timezone.utc)
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            description=description.strip() if description else None,
            icon=icon,
            is_active=True,
            require_all_complete=require_all_complete,
            sort_order=sort_order,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        is_active: Optional[bool] = None,
        require_all_complete: Optional[bool] = None,
        sort_order: Optional[int] = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValueError("Template name is required")
            self.name = name.strip()
        if description is not None:
            self.description = description.strip() if description else None
        if icon is not None:
            self.icon = icon
        if is_active is not None:
            self.is_active = is_active
        if require_all_complete is not None:
            self.require_all_complete = require_all_complete
        if sort_order is not None:
            self.sort_order = sort_order
        self.updated_at = datetime.now(timezone.utc)

    def set_subtypes(self, subtypes: list[WorkflowSubtype]) -> None:
        self.subtypes = subtypes
        self.updated_at = datetime.now(timezone.utc)

    def set_checklist_items(self, items: list[ChecklistItemDefinition]) -> None:
        self.checklist_items = items
        self.updated_at = datetime.now(timezone.utc)
