from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateAssetTypeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    icon: Optional[str] = Field(default=None, max_length=100)


class UpdateAssetTypeRequest(BaseModel):
    name: Optional[str] = Field(
        default=None, min_length=1, max_length=255
    )
    icon: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class ReorderAssetTypesRequest(BaseModel):
    type_ids: list[str]


class AssetTypeResponse(BaseModel):
    id: str
    code: str
    name: str
    icon: Optional[str]
    is_active: bool
    sort_order: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
