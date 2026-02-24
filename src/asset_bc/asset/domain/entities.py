from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import ulid

from src.asset_bc.asset.domain.enums import (
    AssetStatus,
    InvalidStatusTransitionError,
    VALID_TRANSITIONS,
)


class InvalidAssignmentError(Exception):
    pass


@dataclass
class AssetLocation:
    id: str
    company_id: str
    name: str
    is_system: bool
    system_key: Optional[str] = None
    in_use: bool = True
    street_line_1: Optional[str] = None
    street_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_personal: bool = False
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def has_address(self) -> bool:
        return bool(self.street_line_1 and self.city and self.country)

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        is_system: bool = False,
        system_key: Optional[str] = None,
        in_use: bool = True,
        id: Optional[str] = None,
        street_line_1: Optional[str] = None,
        street_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        phone: Optional[str] = None,
        is_personal: bool = False,
        user_id: Optional[str] = None,
    ) -> "AssetLocation":
        if not name or not name.strip():
            raise ValueError("Location name is required")
        if is_system and not system_key:
            raise ValueError("System locations require a system_key")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            is_system=is_system,
            system_key=system_key,
            in_use=in_use,
            street_line_1=street_line_1,
            street_line_2=street_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            phone=phone,
            is_personal=is_personal,
            user_id=user_id,
        )


@dataclass
class Asset:
    id: str
    company_id: str
    type: str
    brand: str
    model: str
    serial_number: str
    status: AssetStatus
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    purchase_cost_cents: Optional[int] = None
    location_id: Optional[str] = None
    custom_fields_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        type: str,
        brand: str,
        model: str,
        serial_number: str,
        purchase_date: Optional[date] = None,
        warranty_expiration: Optional[date] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
        custom_fields_data: Optional[dict] = None,
    ) -> "Asset":
        if not brand or not brand.strip():
            raise ValueError("Brand is required")
        if not model or not model.strip():
            raise ValueError("Model is required")
        if not serial_number or not serial_number.strip():
            raise ValueError("Serial number is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            type=type,
            brand=brand.strip(),
            model=model.strip(),
            serial_number=serial_number.strip(),
            status=AssetStatus.IN_STOCK,
            purchase_date=purchase_date,
            warranty_expiration=warranty_expiration,
            notes=notes.strip() if notes else None,
            custom_fields_data=custom_fields_data or {},
        )

    def update(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        notes: Optional[str] = None,
        purchase_date: Optional[date] = None,
        warranty_expiration: Optional[date] = None,
        custom_fields_data: Optional[dict] = None,
        type: Optional[str] = None,
    ) -> dict:
        changes = {}
        if custom_fields_data is not None:
            self.custom_fields_data = custom_fields_data
        if type is not None:
            old = self.type
            self.type = type
            if old != self.type:
                changes["type"] = {"old": old, "new": self.type}
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
            old_notes = self.notes
            self.notes = notes.strip() if notes else None
            if old_notes != self.notes:
                changes["notes"] = {"old": old_notes or "", "new": self.notes or ""}
        if purchase_date is not None:
            old_purchase = self.purchase_date
            self.purchase_date = purchase_date
            if old_purchase != self.purchase_date:
                old_str = str(old_purchase) if old_purchase else ""
                changes["purchase_date"] = {"old": old_str, "new": str(self.purchase_date)}
        if warranty_expiration is not None:
            old_warranty = self.warranty_expiration
            self.warranty_expiration = warranty_expiration
            if old_warranty != self.warranty_expiration:
                old_str = str(old_warranty) if old_warranty else ""
                changes["warranty_expiration"] = {"old": old_str, "new": str(self.warranty_expiration)}
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

    def move_to(self, location_id: str) -> dict:
        if self.location_id == location_id:
            return {}
        old_location_id = self.location_id
        self.location_id = location_id
        return {"old_location_id": old_location_id, "new_location_id": location_id}

    def change_status(self, new_status: AssetStatus) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(self.status, new_status)
        self.status = new_status
        if new_status == AssetStatus.DECOMMISSIONED:
            self.assigned_to = None
            self.department_id = None
            self.location_id = None


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
