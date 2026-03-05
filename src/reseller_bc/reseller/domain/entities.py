import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    InvalidCommissionRateException,
    InvalidMinPayoutException,
    ResellerOAuthProviderAlreadyLinkedError,
    ResellerPendingApprovalException,
)


def _generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@dataclass
class Reseller:
    id: str
    email: str
    name: str
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None
    avatar_url: Optional[str] = None
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    commission_pct: int = 40
    min_payout_cents: int = 5000
    referral_code: str = ""
    password_hash: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires_at: Optional[datetime] = None
    status: ResellerStatus = ResellerStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        email: str,
        name: str,
        commission_pct: int,
        min_payout_cents: int,
        id: Optional[str] = None,
        status: Optional[ResellerStatus] = None,
        password_hash: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> "Reseller":
        if not email or "@" not in email:
            raise ValueError("Invalid email format")
        if not name or not name.strip():
            raise ValueError("Name is required")
        if commission_pct < 0 or commission_pct > 100:
            raise InvalidCommissionRateException(commission_pct)
        if min_payout_cents <= 0:
            raise InvalidMinPayoutException(min_payout_cents)

        return cls(
            id=id or str(ulid.new()),
            email=email.lower().strip(),
            name=name.strip(),
            commission_pct=commission_pct,
            min_payout_cents=min_payout_cents,
            referral_code=_generate_referral_code(),
            status=status or ResellerStatus.ACTIVE,
            password_hash=password_hash,
            company_name=company_name.strip() if company_name else None,
        )

    def update_profile(
        self,
        company_name: Optional[str] = None,
        tax_id: Optional[str] = None,
    ) -> None:
        if company_name is not None:
            self.company_name = company_name.strip() if company_name else None
        if tax_id is not None:
            self.tax_id = tax_id.strip() if tax_id else None

    def update_settings(
        self,
        commission_pct: Optional[int] = None,
        min_payout_cents: Optional[int] = None,
        status: Optional[ResellerStatus] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        company_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        referral_code: Optional[str] = None,
    ) -> None:
        if name is not None:
            self.name = name.strip()
        if email is not None:
            self.email = email.strip().lower()
        if company_name is not None:
            self.company_name = company_name.strip() if company_name else None
        if tax_id is not None:
            self.tax_id = tax_id.strip() if tax_id else None
        if referral_code is not None:
            self.referral_code = referral_code.strip()
        if commission_pct is not None:
            if commission_pct < 0 or commission_pct > 100:
                raise InvalidCommissionRateException(commission_pct)
            self.commission_pct = commission_pct
        if min_payout_cents is not None:
            if min_payout_cents <= 0:
                raise InvalidMinPayoutException(min_payout_cents)
            self.min_payout_cents = min_payout_cents
        if status is not None:
            self.status = status

    def suspend(self) -> None:
        self.status = ResellerStatus.SUSPENDED

    def activate(self) -> None:
        self.status = ResellerStatus.ACTIVE

    def deactivate(self) -> None:
        self.status = ResellerStatus.DEACTIVATED

    def approve(self) -> None:
        if self.status != ResellerStatus.PENDING:
            raise ResellerPendingApprovalException(
                f"Cannot approve reseller with status: {self.status.value}"
            )
        self.status = ResellerStatus.ACTIVE

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None

    def set_password_hash(self, hashed: str) -> None:
        self.password_hash = hashed

    def set_reset_token(self, token: str, expires_at: datetime) -> None:
        self.reset_token = token
        self.reset_token_expires_at = expires_at

    def clear_reset_token(self) -> None:
        self.reset_token = None
        self.reset_token_expires_at = None

    def link_google(self, google_id: str) -> None:
        if self.google_id is not None and self.google_id != google_id:
            raise ResellerOAuthProviderAlreadyLinkedError("google_id")
        self.google_id = google_id

    def link_microsoft(self, microsoft_id: str) -> None:
        if self.microsoft_id is not None and self.microsoft_id != microsoft_id:
            raise ResellerOAuthProviderAlreadyLinkedError("microsoft_id")
        self.microsoft_id = microsoft_id
