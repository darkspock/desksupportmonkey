from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid

from src.company_bc.company.domain.enums import VALID_TRANSITIONS, CompanyStatus


class InvalidStatusTransitionError(Exception):
    pass


BLOCKED_DOMAINS = frozenset({
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.es", "hotmail.com",
    "hotmail.es", "outlook.com", "outlook.es", "live.com", "aol.com",
    "icloud.com", "me.com", "mac.com", "protonmail.com", "proton.me",
    "zoho.com", "yandex.com", "mail.com", "gmx.com", "gmx.es",
    "mailinator.com", "guerrillamail.com", "tempmail.com",
})


def _normalize_domain(raw: str) -> str:
    """Validate and normalize a domain entry."""
    d = raw.lower().strip()
    if "@" in d:
        raise ValueError(f"'{raw}' looks like an email address, not a domain. Use the part after @, e.g. 'example.com'")
    if not d or "." not in d:
        raise ValueError(f"Invalid domain: '{raw}'")
    if d in BLOCKED_DOMAINS:
        raise ValueError(f"Public email providers like '{d}' are not allowed. Use your company domain.")
    return d


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
            email_domains=[_normalize_domain(d) for d in email_domains],
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
            self.email_domains = [_normalize_domain(d) for d in email_domains]

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
