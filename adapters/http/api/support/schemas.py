from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateTicketRequest(BaseModel):
    category: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    ai_conversation_summary: Optional[str] = None


class AddMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)


class ChangeStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


class ChangePriorityRequest(BaseModel):
    priority: str = Field(..., min_length=1)


class SubmitRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class TicketListItemResponse(BaseModel):
    id: str
    reference: str
    category: str
    subject: str
    status: str
    priority: str
    has_unread: bool = False
    company_id: Optional[str] = None
    created_by_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class TicketDetailResponse(BaseModel):
    id: str
    reference: str
    company_id: str
    created_by: str
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    category: str
    subject: str
    description: str
    status: str
    priority: str
    ai_conversation_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    satisfaction_rating: Optional[int] = None
    satisfaction_comment: Optional[str] = None
    rated_at: Optional[datetime] = None
    messages: list["TicketMessageResponse"] = []


class TicketMessageResponse(BaseModel):
    id: str
    author_id: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    body: str
    is_from_platform: bool
    created_at: Optional[datetime] = None


class TicketStatsResponse(BaseModel):
    open: int = 0
    in_progress: int = 0
    waiting_on_customer: int = 0
    resolved: int = 0
    closed: int = 0
    total: int = 0
    avg_satisfaction_rating: Optional[float] = None
