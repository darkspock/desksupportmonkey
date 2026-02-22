import pytest

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.plan_gate import PlanGate


class TestPlanGateIsFeatureAvailable:
    def test_open_source_mode_bypasses_all(self):
        assert PlanGate.is_feature_available(
            PlanTier.FREE, BillingStatus.SUSPENDED, False, True, "mcp_server"
        ) is True

    def test_complimentary_bypasses_all(self):
        assert PlanGate.is_feature_available(
            PlanTier.FREE, BillingStatus.ACTIVE, True, False, "mcp_server"
        ) is True

    def test_suspended_blocks_feature(self):
        assert PlanGate.is_feature_available(
            PlanTier.ENTERPRISE, BillingStatus.SUSPENDED, False, False, "mcp_server"
        ) is False

    def test_free_plan_has_core_features(self):
        assert PlanGate.is_feature_available(
            PlanTier.FREE, BillingStatus.ACTIVE, False, False, "assets"
        ) is True

    def test_free_plan_lacks_reports(self):
        assert PlanGate.is_feature_available(
            PlanTier.FREE, BillingStatus.ACTIVE, False, False, "reports"
        ) is False

    def test_premium_has_reports(self):
        assert PlanGate.is_feature_available(
            PlanTier.PREMIUM, BillingStatus.ACTIVE, False, False, "reports"
        ) is True

    def test_premium_lacks_mcp(self):
        assert PlanGate.is_feature_available(
            PlanTier.PREMIUM, BillingStatus.ACTIVE, False, False, "mcp_server"
        ) is False

    def test_enterprise_has_mcp(self):
        assert PlanGate.is_feature_available(
            PlanTier.ENTERPRISE, BillingStatus.ACTIVE, False, False, "mcp_server"
        ) is True

    def test_grace_period_still_allows_features(self):
        assert PlanGate.is_feature_available(
            PlanTier.PREMIUM, BillingStatus.GRACE_PERIOD, False, False, "reports"
        ) is True


class TestPlanGateIsWriteAllowed:
    def test_active_allows_writes(self):
        assert PlanGate.is_write_allowed(BillingStatus.ACTIVE, False) is True

    def test_grace_period_allows_writes(self):
        assert PlanGate.is_write_allowed(BillingStatus.GRACE_PERIOD, False) is True

    def test_suspended_blocks_writes(self):
        assert PlanGate.is_write_allowed(BillingStatus.SUSPENDED, False) is False

    def test_over_limit_blocks_writes(self):
        assert PlanGate.is_write_allowed(BillingStatus.OVER_LIMIT, False) is False

    def test_open_source_bypasses_suspended(self):
        assert PlanGate.is_write_allowed(BillingStatus.SUSPENDED, True) is True


class TestPlanGateLimits:
    def test_free_user_limit(self):
        assert PlanGate.get_user_limit(PlanTier.FREE) == 5

    def test_premium_user_limit(self):
        assert PlanGate.get_user_limit(PlanTier.PREMIUM) == 25

    def test_enterprise_user_limit_unlimited(self):
        assert PlanGate.get_user_limit(PlanTier.ENTERPRISE) is None

    def test_open_source_user_limit_unlimited(self):
        assert PlanGate.get_user_limit(PlanTier.OPEN_SOURCE) is None

    def test_free_asset_limit(self):
        assert PlanGate.get_asset_limit(PlanTier.FREE) == 50

    def test_premium_asset_limit(self):
        assert PlanGate.get_asset_limit(PlanTier.PREMIUM) == 500

    def test_enterprise_asset_limit_unlimited(self):
        assert PlanGate.get_asset_limit(PlanTier.ENTERPRISE) is None
