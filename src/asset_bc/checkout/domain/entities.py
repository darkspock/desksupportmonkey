from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.asset_bc.checkout.domain.enums import AssetCondition
from src.asset_bc.checkout.domain.exceptions import (
    CheckoutAlreadyAcceptedError,
    CheckoutNotOpenError,
    UnauthorizedAcceptError,
)


@dataclass
class AssetCheckout:
    id: str
    company_id: str
    asset_id: str
    user_id: str
    checked_out_by: str
    checked_out_at: datetime
    condition_out: AssetCondition
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None
    accepted_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    condition_in: Optional[AssetCondition] = None
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    maintenance_id: Optional[str] = None
    auto_assigned: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        asset_id: str,
        user_id: str,
        checked_out_by: str,
        condition_out: AssetCondition,
        condition_out_notes: Optional[str] = None,
        notes_out: Optional[str] = None,
        id: Optional[str] = None,
        auto_assigned: bool = False,
    ) -> "AssetCheckout":
        if not asset_id:
            raise ValueError("asset_id is required")
        if not user_id:
            raise ValueError("user_id is required")
        if not checked_out_by:
            raise ValueError("checked_out_by is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            asset_id=asset_id,
            user_id=user_id,
            checked_out_by=checked_out_by,
            checked_out_at=datetime.utcnow(),
            condition_out=condition_out,
            condition_out_notes=condition_out_notes.strip() if condition_out_notes else None,
            notes_out=notes_out.strip() if notes_out else None,
            auto_assigned=auto_assigned,
        )

    @property
    def is_open(self) -> bool:
        return self.checked_in_at is None and self.cancelled_at is None

    @property
    def is_accepted(self) -> bool:
        return self.accepted_at is not None

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None

    @property
    def status(self) -> str:
        if self.cancelled_at is not None:
            return "cancelled"
        if self.checked_in_at is not None:
            return "checked_in"
        if self.accepted_at is not None:
            return "accepted"
        return "open"

    def accept(self, user_id: str) -> None:
        if not self.is_open:
            raise CheckoutNotOpenError()
        if self.user_id != user_id:
            raise UnauthorizedAcceptError()
        if self.is_accepted:
            raise CheckoutAlreadyAcceptedError()
        self.accepted_at = datetime.utcnow()

    def checkin(
        self,
        checked_in_by: str,
        condition_in: AssetCondition,
        condition_in_notes: Optional[str] = None,
        notes_in: Optional[str] = None,
    ) -> None:
        if not self.is_open:
            raise CheckoutNotOpenError()
        self.checked_in_at = datetime.utcnow()
        self.checked_in_by = checked_in_by
        self.condition_in = condition_in
        self.condition_in_notes = condition_in_notes.strip() if condition_in_notes else None
        self.notes_in = notes_in.strip() if notes_in else None

    def cancel(self, cancelled_by: str, reason: Optional[str] = None) -> None:
        if not self.is_open:
            raise CheckoutNotOpenError()
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by
        self.cancel_reason = reason.strip() if reason else None
