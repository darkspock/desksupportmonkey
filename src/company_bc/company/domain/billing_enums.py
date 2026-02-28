from enum import Enum


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    OPEN_SOURCE = "open_source"


class BillingStatus(str, Enum):
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    SUSPENDED = "suspended"
    OVER_LIMIT = "over_limit"
