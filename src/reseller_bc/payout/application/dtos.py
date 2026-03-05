from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PayoutDto:
    id: str
    reseller_id: str
    reseller_name: str
    amount_cents: int
    status: str
    requested_at: Optional[datetime]
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]


@dataclass
class PayoutListDto:
    items: list[PayoutDto]
    total: int
