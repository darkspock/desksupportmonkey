from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import ulid

from src.asset_bc.asset.domain.enums import (
    AssetStatus,
    AssetType,
    InvalidStatusTransitionError,
    VALID_TRANSITIONS,
)


class InvalidAssignmentError(Exception):
    pass


@dataclass
class Asset:
    id: str
    company_id: str
    type: AssetType
    brand: str
    model: str
    serial_number: str
    status: AssetStatus
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        type: AssetType,
        brand: str,
        model: str,
        serial_number: str,
        purchase_date: Optional[date] = None,
        warranty_expiration: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> "Asset":
        if not brand or not brand.strip():
            raise ValueError("Brand is required")
        if not model or not model.strip():
            raise ValueError("Model is required")
        if not serial_number or not serial_number.strip():
            raise ValueError("Serial number is required")
        return cls(
            id=str(ulid.new()),
            company_id=company_id,
            type=type,
            brand=brand.strip(),
            model=model.strip(),
            serial_number=serial_number.strip(),
            status=AssetStatus.IN_STOCK,
            purchase_date=purchase_date,
            warranty_expiration=warranty_expiration,
            notes=notes.strip() if notes else None,
        )

    def update(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        notes: Optional[str] = None,
        purchase_date: Optional[date] = None,
        warranty_expiration: Optional[date] = None,
    ) -> dict:
        changes = {}
        if brand is not None:
            if not brand.strip():
                raise ValueError("Brand cannot be empty")
            old = self.brand
            self.brand = brand.strip()
            if old != self.brand:
                changes["brand"] = {"old": old, "new": self.brand}
        if model is not None:
            if not model.strip():
                raise ValueError("Model cannot be empty")
            old = self.model
            self.model = model.strip()
            if old != self.model:
                changes["model"] = {"old": old, "new": self.model}
        if notes is not None:
            old = self.notes
            self.notes = notes.strip() if notes else None
            if old != self.notes:
                changes["notes"] = {"old": old, "new": self.notes}
        if purchase_date is not None:
            old = self.purchase_date
            self.purchase_date = purchase_date
            if old != self.purchase_date:
                changes["purchase_date"] = {"old": str(old) if old else None, "new": str(self.purchase_date)}
        if warranty_expiration is not None:
            old = self.warranty_expiration
            self.warranty_expiration = warranty_expiration
            if old != self.warranty_expiration:
                changes["warranty_expiration"] = {"old": str(old) if old else None, "new": str(self.warranty_expiration)}
        return changes

    def assign(self, user_id: str, department_id: Optional[str] = None) -> None:
        if self.status != AssetStatus.IN_STOCK:
            raise InvalidAssignmentError("Asset must be in stock to assign")
        self.assigned_to = user_id
        self.department_id = department_id
        self.status = AssetStatus.ASSIGNED

    def unassign(self) -> None:
        if self.status != AssetStatus.ASSIGNED:
            raise InvalidAssignmentError("Asset is not currently assigned")
        self.assigned_to = None
        self.department_id = None
        self.status = AssetStatus.IN_STOCK

    def change_status(self, new_status: AssetStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(self.status, new_status)
        self.status = new_status
        if new_status == AssetStatus.DECOMMISSIONED:
            self.assigned_to = None
            self.department_id = None


@dataclass
class AssetEvent:
    id: str
    asset_id: str
    event_type: str
    data: dict
    performed_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        asset_id: str,
        event_type: str,
        data: dict,
        performed_by: str,
    ) -> "AssetEvent":
        return cls(
            id=str(ulid.new()),
            asset_id=asset_id,
            event_type=event_type,
            data=data,
            performed_by=performed_by,
        )
