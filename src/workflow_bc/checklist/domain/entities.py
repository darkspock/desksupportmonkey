from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid


@dataclass
class RequestChecklistItem:
    id: str
    request_id: str
    require_all_complete: bool
    title: str
    description: Optional[str]
    assignee_id: Optional[str]
    is_required: bool
    is_completed: bool
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    sort_order: int
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        request_id: str,
        title: str,
        require_all_complete: bool = False,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        is_required: bool = True,
        sort_order: int = 0,
    ) -> "RequestChecklistItem":
        if not title or not title.strip():
            raise ValueError("Checklist item title is required")
        return cls(
            id=str(ulid.new()),
            request_id=request_id,
            require_all_complete=require_all_complete,
            title=title.strip(),
            description=description.strip() if description else None,
            assignee_id=assignee_id,
            is_required=is_required,
            is_completed=False,
            completed_by=None,
            completed_at=None,
            sort_order=sort_order,
            created_at=datetime.now(timezone.utc),
        )

    def toggle(self, user_id: str) -> None:
        if self.is_completed:
            self.is_completed = False
            self.completed_by = None
            self.completed_at = None
        else:
            self.is_completed = True
            self.completed_by = user_id
            self.completed_at = datetime.now(timezone.utc)

    def assign(self, assignee_id: Optional[str]) -> None:
        self.assignee_id = assignee_id
