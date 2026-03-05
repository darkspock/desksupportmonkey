import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import ulid

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.enums import AuthMode, VALID_TRANSITIONS, CompanyStatus, CompanySector


class InvalidStatusTransitionError(Exception):
    pass


class InvalidSectorError(Exception):
    pass


class InvalidSlugError(Exception):
    pass


class NoAdminMembershipError(Exception):
    """Cannot switch to membership_only with no admin memberships."""
    pass


class SlugAlreadyTakenError(Exception):
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Slug '{slug}' is already taken")


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
    if d.startswith("@"):
        d = d[1:].strip()
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
    # Billing fields
    plan: PlanTier = PlanTier.FREE
    billing_status: BillingStatus = BillingStatus.ACTIVE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    grace_period_started_at: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    pending_downgrade_plan: Optional[PlanTier] = None
    complimentary: bool = False
    trial_ends_at: Optional[datetime] = None
    # Onboarding fields
    sector: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None
    # Auth fields
    slug: Optional[str] = None
    auth_mode: AuthMode = AuthMode.DOMAIN

    def is_in_trial(self) -> bool:
        if self.trial_ends_at is None:
            return False
        if self.trial_ends_at.tzinfo is None:
            trial_end = self.trial_ends_at.replace(tzinfo=timezone.utc)
        else:
            trial_end = self.trial_ends_at
        return datetime.now(timezone.utc) < trial_end

    @property
    def is_demo_account(self) -> bool:
        return self.plan == PlanTier.DEMO

    @property
    def demo_days_remaining(self) -> Optional[int]:
        """Days remaining in the demo period, or None if not a demo."""
        if self.plan != PlanTier.DEMO or self.trial_ends_at is None:
            return None
        trial_end = self.trial_ends_at
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)
        remaining = (trial_end - datetime.now(timezone.utc)).days
        return max(0, remaining)

    def activate_from_demo(
        self,
        name: Optional[str] = None,
        email_domains: Optional[list[str]] = None,
    ) -> None:
        """Convert a demo company to a real FREE account."""
        if self.plan != PlanTier.DEMO:
            raise ValueError("Company is not a demo account")
        self.plan = PlanTier.FREE
        self.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=15)
        if name is not None:
            if not name.strip():
                raise ValueError("Company name is required")
            self.name = name.strip()
        if email_domains is not None:
            if not email_domains:
                raise ValueError("At least one email domain is required")
            self.email_domains = [_normalize_domain(d) for d in email_domains]

    @classmethod
    def create(
        cls,
        name: str,
        email_domains: list[str],
        id: Optional[str] = None,
        open_source_mode: bool = False,
        slug: Optional[str] = None,
        is_demo: bool = False,
    ) -> "Company":
        if not name or not name.strip():
            raise ValueError("Company name is required")
        if not email_domains:
            raise ValueError("At least one email domain is required")
        if slug:
            cls.validate_slug(slug)
        if is_demo:
            plan = PlanTier.DEMO
            trial_ends_at = datetime.now(timezone.utc) + timedelta(days=14)
        elif open_source_mode:
            plan = PlanTier.OPEN_SOURCE
            trial_ends_at = None
        else:
            plan = PlanTier.FREE
            trial_ends_at = datetime.now(timezone.utc) + timedelta(days=15)
        return cls(
            id=id or str(ulid.new()),
            name=name.strip(),
            status=CompanyStatus.ACTIVE,
            email_domains=[_normalize_domain(d) for d in email_domains],
            is_active=True,
            plan=plan,
            trial_ends_at=trial_ends_at,
            slug=slug,
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

    # ------------------------------------------------------------------
    # Billing domain methods
    # ------------------------------------------------------------------

    def set_billing_status(self, status: BillingStatus) -> None:
        self.billing_status = status

    def apply_plan_change(
        self,
        plan: PlanTier,
        subscription_id: str,
        period_end: datetime,
    ) -> None:
        self.plan = plan
        self.stripe_subscription_id = subscription_id
        self.current_period_end = period_end
        self.billing_status = BillingStatus.ACTIVE
        self.grace_period_started_at = None
        self.pending_downgrade_plan = None

    def enter_grace_period(self) -> None:
        self.billing_status = BillingStatus.GRACE_PERIOD
        self.grace_period_started_at = datetime.now(timezone.utc)

    def restore_billing(self) -> None:
        self.billing_status = BillingStatus.ACTIVE
        self.grace_period_started_at = None

    def grant_complimentary(self, plan: PlanTier) -> None:
        self.complimentary = True
        self.plan = plan
        self.billing_status = BillingStatus.ACTIVE
        self.stripe_subscription_id = None
        self.grace_period_started_at = None

    def revoke_complimentary(self) -> None:
        self.complimentary = False
        self.plan = PlanTier.FREE
        self.billing_status = BillingStatus.OVER_LIMIT

    # ------------------------------------------------------------------
    # Onboarding domain methods
    # ------------------------------------------------------------------

    def set_sector(self, sector: Optional[str]) -> None:
        if sector is not None:
            valid = {s.value for s in CompanySector}
            if sector not in valid:
                raise InvalidSectorError(f"Invalid sector: '{sector}'")
        self.sector = sector

    def complete_onboarding(self) -> None:
        self.onboarding_completed_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Slug domain methods
    # ------------------------------------------------------------------

    RESERVED_SLUGS = frozenset({
        'admin', 'api', 'login', 'register', 'app', 'auth', 'super-admin',
    })

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-safe slug from company name. NFKD normalization -> ASCII -> lowercase + hyphens."""
        normalized = unicodedata.normalize('NFKD', name)
        ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')
        if len(slug) < 3:
            slug = slug + '-co'
        return slug[:50]

    @staticmethod
    def validate_slug(slug: str) -> None:
        """Validate slug format. Raises ValueError if invalid."""
        if not slug:
            raise ValueError("Slug is required")
        if len(slug) < 3 or len(slug) > 50:
            raise ValueError("Slug must be between 3 and 50 characters")
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
        if slug in Company.RESERVED_SLUGS:
            raise ValueError(f"Slug '{slug}' is reserved")

    def update_slug(self, slug: str) -> None:
        """Update the company slug after validation."""
        Company.validate_slug(slug)
        self.slug = slug

    # ------------------------------------------------------------------
    # Auth mode methods
    # ------------------------------------------------------------------

    def set_auth_mode(self, mode: AuthMode) -> None:
        """Change the company's authentication mode."""
        self.auth_mode = mode
