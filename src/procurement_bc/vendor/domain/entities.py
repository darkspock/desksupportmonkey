from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class Vendor:
    id: str
    company_id: str
    name: str
    is_active: bool = True
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        contact_email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "Vendor":
        if not name or not name.strip():
            raise ValueError("Vendor name is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            is_active=True,
            contact_email=contact_email,
            phone=phone,
            address=address,
            notes=notes,
        )

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
