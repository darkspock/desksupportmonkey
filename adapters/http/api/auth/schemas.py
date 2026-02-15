from typing import Optional

from pydantic import BaseModel, EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr

    model_config = {"json_schema_extra": {"examples": [{"email": "user@company.com"}]}}


class VerifyRequest(BaseModel):
    token: str

    model_config = {"json_schema_extra": {"examples": [{"token": "abc123..."}]}}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str
    company_id: Optional[str] = None
    is_active: bool
