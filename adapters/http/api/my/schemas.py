from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MyEquipmentResponse(BaseModel):
    id: str
    type: str
    brand: str
    model: str
    serial_number: str
    created_at: Optional[datetime] = None
