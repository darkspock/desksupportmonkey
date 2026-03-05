from pydantic import BaseModel, EmailStr, Field


class RegisterCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    admin_email: EmailStr
    email_domains: list[str] = Field(min_length=1)
    referral_code: str | None = None
