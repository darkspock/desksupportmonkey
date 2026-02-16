from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateRequestRequest(BaseModel):
    type: str
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    data: Optional[dict] = None


class ChangeStatusRequest(BaseModel):
    status: str


class ChangePriorityRequest(BaseModel):
    priority: str


class AssignRequestRequest(BaseModel):
    user_id: str = Field(min_length=1)


class RequestListItemResponse(BaseModel):
    id: str
    type: str
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_to_email: Optional[str] = None
    created_by: str
    created_by_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AddCommentRequest(BaseModel):
    body: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: str
    request_id: str
    author_id: str
    author_email: Optional[str] = None
    body: str
    created_at: Optional[datetime] = None


class NoteResponse(BaseModel):
    id: str
    request_id: str
    author_id: str
    author_email: Optional[str] = None
    body: str
    created_at: Optional[datetime] = None


class RequestResponse(BaseModel):
    id: str
    company_id: str
    created_by: str
    created_by_email: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_email: Optional[str] = None
    type: str
    title: str
    description: str
    status: str
    priority: str
    data: Optional[dict] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comment_count: int = 0
