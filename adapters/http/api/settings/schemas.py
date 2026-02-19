from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SaveAIConfigRequest(BaseModel):
    provider: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    model: Optional[str] = Field(
        default=None, max_length=100,
    )


class AIConfigResponse(BaseModel):
    id: str
    company_id: str
    provider: str
    prompt_template: str
    model: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
