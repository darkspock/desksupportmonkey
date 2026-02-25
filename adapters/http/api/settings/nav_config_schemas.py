from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class SaveNavConfigRequest(BaseModel):
    hidden_nav_items: Dict[str, List[str]] = {}


class NavConfigResponse(BaseModel):
    id: str
    company_id: str
    hidden_nav_items: Dict[str, List[str]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
