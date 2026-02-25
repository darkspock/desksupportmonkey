from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubtypeRequest(BaseModel):
    id: Optional[str] = None
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    sort_order: int = 0
    is_active: bool = True


class ChecklistItemDefinitionRequest(BaseModel):
    id: Optional[str] = None
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    assignee_role: Optional[str] = Field(default=None, max_length=30)
    sort_order: int = 0
    is_required: bool = True


class CreateWorkflowTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, max_length=50)
    require_all_complete: bool = False
    sort_order: int = 0
    subtypes: list[SubtypeRequest] = Field(default_factory=list)
    checklist_items: list[ChecklistItemDefinitionRequest] = Field(default_factory=list)


class UpdateWorkflowTemplateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    require_all_complete: Optional[bool] = None
    sort_order: Optional[int] = None
    subtypes: Optional[list[SubtypeRequest]] = None
    checklist_items: Optional[list[ChecklistItemDefinitionRequest]] = None


class SubtypeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    sort_order: int
    is_active: bool


class ChecklistItemDefinitionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    assignee_role: Optional[str]
    sort_order: int
    is_required: bool


class WorkflowTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    is_active: bool
    require_all_complete: bool
    sort_order: int
    subtypes: list[SubtypeResponse]
    checklist_items: list[ChecklistItemDefinitionResponse]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
