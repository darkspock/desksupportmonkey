from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateRequestRequest(BaseModel):
    type: str
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    subtype: Optional[str] = None
    data: Optional[dict] = None
    on_behalf_of: Optional[str] = None
    custom_fields_data: Optional[dict[str, Any]] = None
    template_id: Optional[str] = None


class ChangeStatusRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class ChangePriorityRequest(BaseModel):
    priority: str


class AssignRequestRequest(BaseModel):
    user_id: str = Field(min_length=1)


class RequestListItemResponse(BaseModel):
    id: str
    type: str
    subtype: Optional[str] = None
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_to_email: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    custom_fields: Optional[list[dict[str, Any]]] = None
    workflow_template_name: Optional[str] = None
    workflow_template_icon: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RejectRequestRequest(BaseModel):
    reason: str = Field(min_length=1)


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


class RequestEventResponse(BaseModel):
    id: str
    request_id: str
    event_type: str
    data: Optional[dict[str, Any]] = None
    performed_by: str
    performed_by_name: Optional[str] = None
    performed_by_email: Optional[str] = None
    created_at: Optional[datetime] = None


class RequestResponse(BaseModel):
    id: str
    company_id: str
    created_by: str
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_to_email: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    title: str
    description: str
    status: str
    priority: str
    data: Optional[dict] = None
    custom_fields: Optional[list[dict[str, Any]]] = None
    workflow_template_id: Optional[str] = None
    workflow_template_name: Optional[str] = None
    workflow_template_icon: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comment_count: int = 0


class SetAffectedAssetsRequest(BaseModel):
    asset_ids: list[str]


class RequesterAssetResponse(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    type: str
    criticality: Optional[str] = None
    status: str
    is_affected: bool
