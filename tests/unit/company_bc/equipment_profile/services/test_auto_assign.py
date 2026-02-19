"""Tests for AutoAssignService."""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from unittest.mock import MagicMock

from src.asset_bc.asset.domain.enums import AssetType
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.assignment_config.domain.enums import (
    FallbackReason,
)
from src.company_bc.equipment_profile.application.services.auto_assign import (  # noqa: E501
    AutoAssignService,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
    EquipmentProfileItem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class FakeAsset:
    id: str
    brand: str = "Dell"
    model: str = "Latitude"
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


def _build_service(
    profile=None,
    config=None,
    assets=None,
):
    profile_repo = MagicMock()
    profile_repo.find_active.return_value = profile

    config_repo = MagicMock()
    config_repo.find_by_company.return_value = config

    asset_lookup = MagicMock()
    if assets is not None:
        asset_lookup.find_in_stock_by_type.return_value = assets
    else:
        asset_lookup.find_in_stock_by_type.return_value = []

    ai_settings = MagicMock()
    ai_settings.OPENAI_API_KEY = ""
    ai_settings.GROQ_API_KEY = ""

    svc = AutoAssignService(
        profile_repo=profile_repo,
        config_repo=config_repo,
        asset_lookup=asset_lookup,
        ai_settings=ai_settings,
    )
    return svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAutoAssignSuccess:
    def test_auto_assign_success_stores_metadata(self):
        """Matched assets appear in metadata."""
        profile = EquipmentProfile.create(
            company_id="c1",
            department_id="d1",
            role=UserRole.EMPLOYEE,
        )
        profile.items = [
            EquipmentProfileItem(
                id="i1",
                profile_id=profile.id,
                asset_type=AssetType.LAPTOP,
                quantity=1,
            ),
        ]
        asset = FakeAsset(id="a1")

        svc = _build_service(
            profile=profile, assets=[asset],
        )
        result = svc.attempt_assignment(
            company_id="c1",
            department_id="d1",
            role="employee",
        )

        assert result["status"] == "matched"
        assert len(result["matched_assets"]) == 1
        assert (
            result["matched_assets"][0]["asset_id"] == "a1"
        )


class TestAutoAssignFallback:
    def test_auto_assign_fallback_stores_reasons(self):
        """No profile → fallback with reasons."""
        svc = _build_service(profile=None)
        result = svc.attempt_assignment(
            company_id="c1",
            department_id="d1",
            role="employee",
        )

        assert result["status"] == "fallback"
        assert (
            FallbackReason.NO_ACTIVE_PROFILE.value
            in result["reasons"]
        )


class TestAutoAssignSkips:
    def test_auto_assign_skips_no_department(self):
        """No department → skip."""
        svc = _build_service()
        result = svc.attempt_assignment(
            company_id="c1",
            department_id=None,
            role="employee",
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "no_department_or_role"

    def test_auto_assign_skips_no_role(self):
        """No role → skip."""
        svc = _build_service()
        result = svc.attempt_assignment(
            company_id="c1",
            department_id="d1",
            role=None,
        )

        assert result["status"] == "skipped"
