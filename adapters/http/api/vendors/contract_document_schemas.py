from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    contract_id: str
    company_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_by: str
    created_at: Optional[datetime] = None
