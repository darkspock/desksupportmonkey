from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.reseller_bc.payout.domain.enums import PayoutStatus
from src.reseller_bc.payout.domain.exceptions import (
    InvalidPayoutAmountException,
    InvalidPayoutTransitionException,
)


@dataclass
class ResellerPayout:
    id: str
    reseller_id: str
    amount_cents: int
    status: PayoutStatus
    requested_at: Optional[datetime]
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]

    @classmethod
    def create(cls, reseller_id: str, amount_cents: int, id: Optional[str] = None) -> "ResellerPayout":
        if amount_cents <= 0:
            raise InvalidPayoutAmountException(amount_cents)
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            amount_cents=amount_cents,
            status=PayoutStatus.REQUESTED,
            requested_at=datetime.utcnow(),
            processed_at=None,
            processed_by=None,
            payment_reference=None,
            notes=None,
        )

    def approve(self, processed_by: str) -> None:
        if self.status != PayoutStatus.REQUESTED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.APPROVED.value)
        self.status = PayoutStatus.APPROVED
        self.processed_at = datetime.utcnow()
        self.processed_by = processed_by

    def reject(self, processed_by: str, notes: Optional[str] = None) -> None:
        if self.status != PayoutStatus.REQUESTED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.REJECTED.value)
        self.status = PayoutStatus.REJECTED
        self.processed_at = datetime.utcnow()
        self.processed_by = processed_by
        self.notes = notes

    def mark_paid(self, payment_reference: str) -> None:
        if self.status != PayoutStatus.APPROVED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.PAID.value)
        self.status = PayoutStatus.PAID
        self.payment_reference = payment_reference
        self.processed_at = datetime.utcnow()
