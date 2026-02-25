from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AddChecklistItemRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    assignee_id: Optional[str] = None
    is_required: bool = False


class AssignChecklistItemRequest(BaseModel):
    assignee_id: Optional[str] = None


class ChecklistItemResponse(BaseModel):
    id: str
    request_id: str
    title: str
    description: Optional[str]
    assignee_id: Optional[str]
    is_required: bool
    is_completed: bool
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    sort_order: int
    created_at: Optional[datetime]


class ChecklistProgressResponse(BaseModel):
    total: int
    completed: int
    required_remaining: int
