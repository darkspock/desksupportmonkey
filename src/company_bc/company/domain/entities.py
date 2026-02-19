from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid

from src.company_bc.company.domain.enums import VALID_TRANSITIONS, CompanyStatus


class InvalidStatusTransitionError(Exception):
    pass


@dataclass
class Company:
    id: str
    name: str
    status: CompanyStatus
    email_domains: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, name: str, email_domains: list[str], id: Optional[str] = None) -> "Company":
        if not name or not name.strip():
            raise ValueError("Company name is required")
        if not email_domains:
            raise ValueError("At least one email domain is required")
        return cls(
            id=id or str(ulid.new()),
            name=name.strip(),
            status=CompanyStatus.ACTIVE,
            email_domains=[d.lower().strip() for d in email_domains],
            is_active=True,
        )

    def update(
        self,
        name: Optional[str] = None,
        email_domains: Optional[list[str]] = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValueError("Company name is required")
            self.name = name.strip()
        if email_domains is not None:
            if not email_domains:
                raise ValueError("At least one email domain is required")
            self.email_domains = [d.lower().strip() for d in email_domains]

    def change_status(self, new_status: CompanyStatus) -> None:
        if new_status == self.status:
            raise InvalidStatusTransitionError(
                f"Company is already {self.status.value}"
            )
        if new_status not in VALID_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(
                f"Cannot transition from '{self.status.value}' to '{new_status.value}'"
            )
        self.status = new_status
        self.is_active = new_status == CompanyStatus.ACTIVE
