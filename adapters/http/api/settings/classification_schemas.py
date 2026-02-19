from typing import Optional

from pydantic import BaseModel, Field


class SaveClassificationConfigRequest(BaseModel):
    is_enabled: bool
    provider: str = Field(min_length=1)
    model: Optional[str] = Field(default=None, max_length=100)
    confidence_threshold: float = Field(ge=0.5, le=1.0, default=0.7)
    prompt_template: Optional[str] = Field(default=None)
    timeout_seconds: int = Field(ge=1, le=60, default=10)


class ClassificationConfigResponse(BaseModel):
    id: str
    company_id: str
    is_enabled: bool
    provider: str
    model: Optional[str] = None
    confidence_threshold: float
    prompt_template: Optional[str] = None
    timeout_seconds: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
