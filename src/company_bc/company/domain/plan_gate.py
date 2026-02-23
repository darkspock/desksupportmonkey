from typing import Optional

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier

# Features available per plan (cumulative)
_FREE_FEATURES: set[str] = {
    "core", "assets", "requests", "dashboard", "magic_link", "password_login",
}
_PREMIUM_FEATURES: set[str] = _FREE_FEATURES | {
    "reports", "oauth_login", "api_keys", "ai_classification",
    "appointments", "shipments", "maintenance", "procurement",
}
_ENTERPRISE_FEATURES: set[str] = _PREMIUM_FEATURES | {
    "mcp_server", "sso", "audit_trail", "custom_fields",
    "automations", "sla", "knowledge_base", "onboarding",
}

PLAN_FEATURES: dict[PlanTier, set[str]] = {
    PlanTier.FREE: _FREE_FEATURES,
    PlanTier.PREMIUM: _PREMIUM_FEATURES,
    PlanTier.ENTERPRISE: _ENTERPRISE_FEATURES,
    PlanTier.OPEN_SOURCE: set(),  # all allowed — bypass in logic
}

PLAN_USER_LIMITS: dict[PlanTier, Optional[int]] = {
    PlanTier.FREE: 5,
    PlanTier.PREMIUM: 25,
    PlanTier.ENTERPRISE: None,
    PlanTier.OPEN_SOURCE: None,
}

PLAN_ASSET_LIMITS: dict[PlanTier, Optional[int]] = {
    PlanTier.FREE: 50,
    PlanTier.PREMIUM: 500,
    PlanTier.ENTERPRISE: None,
    PlanTier.OPEN_SOURCE: None,
}


class PlanGate:

    @staticmethod
    def is_feature_available(
        plan: PlanTier,
        billing_status: BillingStatus,
        complimentary: bool,
        open_source_mode: bool,
        feature: str,
        in_trial: bool = False,
    ) -> bool:
        if open_source_mode or complimentary or in_trial:
            return True
        if billing_status == BillingStatus.SUSPENDED:
            return False
        return feature in PLAN_FEATURES.get(plan, set())

    @staticmethod
    def is_write_allowed(
        billing_status: BillingStatus,
        open_source_mode: bool,
        in_trial: bool = False,
    ) -> bool:
        if open_source_mode or in_trial:
            return True
        return billing_status not in (BillingStatus.SUSPENDED, BillingStatus.OVER_LIMIT)

    @staticmethod
    def get_user_limit(plan: PlanTier, in_trial: bool = False) -> Optional[int]:
        if in_trial:
            return None
        return PLAN_USER_LIMITS.get(plan)

    @staticmethod
    def get_asset_limit(plan: PlanTier, in_trial: bool = False) -> Optional[int]:
        if in_trial:
            return None
        return PLAN_ASSET_LIMITS.get(plan)
