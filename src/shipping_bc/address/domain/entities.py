from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid


@dataclass
class ShippingAddress:
    id: str
    company_id: str
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        label: str,
        street_line_1: str,
        city: str,
        state: str,
        postal_code: str,
        country: str = "US",
        street_line_2: Optional[str] = None,
        recipient_name: Optional[str] = None,
        phone: Optional[str] = None,
        user_id: Optional[str] = None,
        is_office: bool = False,
        id: Optional[str] = None,
    ) -> "ShippingAddress":
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            label=label,
            street_line_1=street_line_1,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            street_line_2=street_line_2,
            recipient_name=recipient_name,
            phone=phone,
            user_id=user_id,
            is_office=is_office,
            is_active=True,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def update(
        self,
        label: Optional[str] = None,
        street_line_1: Optional[str] = None,
        street_line_2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        country: Optional[str] = None,
        recipient_name: Optional[str] = None,
        phone: Optional[str] = None,
        user_id: Optional[str] = None,
        is_office: Optional[bool] = None,
    ) -> None:
        if label is not None:
            self.label = label
        if street_line_1 is not None:
            self.street_line_1 = street_line_1
        if street_line_2 is not None:
            self.street_line_2 = street_line_2
        if city is not None:
            self.city = city
        if state is not None:
            self.state = state
        if postal_code is not None:
            self.postal_code = postal_code
        if country is not None:
            self.country = country
        if recipient_name is not None:
            self.recipient_name = recipient_name
        if phone is not None:
            self.phone = phone
        if user_id is not None:
            self.user_id = user_id
        if is_office is not None:
            self.is_office = is_office
