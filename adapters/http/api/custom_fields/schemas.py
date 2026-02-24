from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateFieldDefinitionRequest(BaseModel):
    entity_type: str = Field(pattern=r"^(asset|request|incident)$")
    label: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    field_type: str = Field(
        pattern=r"^(text|number|date|select|multi_select|boolean|file)$"
    )
    options: Optional[list[str]] = None
    required: bool = False
    visible_to_employees: bool = True


class UpdateFieldDefinitionRequest(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    options: Optional[list[str]] = None
    required: Optional[bool] = None
    visible_to_employees: Optional[bool] = None


class ReorderRequest(BaseModel):
    entity_type: str = Field(pattern=r"^(asset|request|incident)$")
    field_ids: list[str]


class FieldDefinitionResponse(BaseModel):
    id: str
    entity_type: str
    field_key: str
    label: str
    description: Optional[str]
    field_type: str
    options: Optional[list[str]]
    required: bool
    sort_order: int
    is_active: bool
    visible_to_employees: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class FileUploadResponse(BaseModel):
    id: str
    name: str
    size: int
    mime: str
    key: str


class FileDownloadResponse(BaseModel):
    url: str
