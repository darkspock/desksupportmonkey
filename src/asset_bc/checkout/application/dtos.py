from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.asset_bc.checkout.domain.entities import AssetCheckout


@dataclass
class CheckoutDto:
    id: str
    company_id: str
    asset_id: str
    user_id: str
    checked_out_by: str
    checked_out_at: datetime
    condition_out: str
    condition_out_notes: Optional[str]
    notes_out: Optional[str]
    accepted_at: Optional[datetime]
    checked_in_at: Optional[datetime]
    checked_in_by: Optional[str]
    condition_in: Optional[str]
    condition_in_notes: Optional[str]
    notes_in: Optional[str]
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[str]
    cancel_reason: Optional[str]
    maintenance_id: Optional[str]
    auto_assigned: bool
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: AssetCheckout) -> "CheckoutDto":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            asset_id=entity.asset_id,
            user_id=entity.user_id,
            checked_out_by=entity.checked_out_by,
            checked_out_at=entity.checked_out_at,
            condition_out=entity.condition_out.value if hasattr(entity.condition_out, "value") else entity.condition_out,
            condition_out_notes=entity.condition_out_notes,
            notes_out=entity.notes_out,
            accepted_at=entity.accepted_at,
            checked_in_at=entity.checked_in_at,
            checked_in_by=entity.checked_in_by,
            condition_in=entity.condition_in.value if entity.condition_in and hasattr(entity.condition_in, "value") else entity.condition_in,
            condition_in_notes=entity.condition_in_notes,
            notes_in=entity.notes_in,
            cancelled_at=entity.cancelled_at,
            cancelled_by=entity.cancelled_by,
            cancel_reason=entity.cancel_reason,
            maintenance_id=entity.maintenance_id,
            auto_assigned=entity.auto_assigned,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
