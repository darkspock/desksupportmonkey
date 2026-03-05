from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.reseller_bc.commission.domain.enums import CommissionStatus


@dataclass
class ResellerCommission:
    id: str
    reseller_id: str
    reseller_client_id: str
    company_id: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    stripe_invoice_id: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    status: CommissionStatus
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        reseller_id: str,
        reseller_client_id: str,
        company_id: str,
        payment_amount_cents: int,
        commission_pct: int,
        stripe_invoice_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        id: Optional[str] = None,
    ) -> "ResellerCommission":
        commission_amount = payment_amount_cents * commission_pct // 100
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            reseller_client_id=reseller_client_id,
            company_id=company_id,
            payment_amount_cents=payment_amount_cents,
            commission_pct=commission_pct,
            commission_amount_cents=commission_amount,
            stripe_invoice_id=stripe_invoice_id,
            period_start=period_start,
            period_end=period_end,
            status=CommissionStatus.PENDING,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def create_clawback(
        cls,
        original: "ResellerCommission",
        id: Optional[str] = None,
    ) -> "ResellerCommission":
        """Create negative commission for paid-then-refunded scenario."""
        return cls(
            id=id or str(ulid.new()),
            reseller_id=original.reseller_id,
            reseller_client_id=original.reseller_client_id,
            company_id=original.company_id,
            payment_amount_cents=-original.payment_amount_cents,
            commission_pct=original.commission_pct,
            commission_amount_cents=-original.commission_amount_cents,
            stripe_invoice_id=original.stripe_invoice_id,
            period_start=original.period_start,
            period_end=original.period_end,
            status=CommissionStatus.CLAWED_BACK,
            created_at=datetime.utcnow(),
        )

    def confirm(self) -> None:
        self.status = CommissionStatus.CONFIRMED

    def clawback(self) -> None:
        self.status = CommissionStatus.CLAWED_BACK

    def mark_as_paid(self) -> None:
        self.status = CommissionStatus.PAID
