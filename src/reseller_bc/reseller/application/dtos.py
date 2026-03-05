from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.reseller_bc.reseller.domain.entities import Reseller


@dataclass
class ResellerDto:
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    company_name: Optional[str]
    tax_id: Optional[str]
    commission_pct: int
    min_payout_cents: int
    referral_code: str
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: Reseller) -> "ResellerDto":
        return cls(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            avatar_url=entity.avatar_url,
            company_name=entity.company_name,
            tax_id=entity.tax_id,
            commission_pct=entity.commission_pct,
            min_payout_cents=entity.min_payout_cents,
            referral_code=entity.referral_code,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


@dataclass
class ResellerDashboardDto:
    reseller_id: str
    name: str
    referral_code: str
    status: str
    client_count: int
    total_commissions_cents: int
    available_balance_cents: int
    pending_payout_cents: int


@dataclass
class ResellerListDto:
    items: list[ResellerDto]
    total: int
