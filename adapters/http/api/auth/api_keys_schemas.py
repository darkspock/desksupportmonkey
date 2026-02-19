from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool


class CreateApiKeyResponse(BaseModel):
    id: str
    name: str
    raw_key: str
    created_at: datetime
    is_active: bool
