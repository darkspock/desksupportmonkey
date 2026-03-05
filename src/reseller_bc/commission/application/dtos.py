from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommissionDto:
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    stripe_invoice_id: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    status: str
    created_at: Optional[datetime]


@dataclass
class CommissionListDto:
    items: list[CommissionDto]
    total: int
