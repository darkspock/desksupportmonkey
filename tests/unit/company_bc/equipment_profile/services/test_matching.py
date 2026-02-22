"""Tests for EquipmentProfileMatcher."""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from unittest.mock import MagicMock

from src.asset_bc.asset.domain.enums import AssetType
from src.company_bc.assignment_config.domain.enums import (
    FallbackReason,
)
from src.company_bc.equipment_profile.application.services.matching import (  # noqa: E501
    EquipmentProfileMatcher,
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
    """Minimal asset stub for matching tests."""
    id: str
    brand: str = "Dell"
    model: str = "Latitude"
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


def _profile(items: list[EquipmentProfileItem]) -> EquipmentProfile:
    p = EquipmentProfile.create(
        company_id="c1",
        department_id="d1",
        employee_role_id="er1",
    )
    p.items = items
    return p


def _item(
    asset_type: AssetType = AssetType.LAPTOP,
    preferred_brand: Optional[str] = None,
    preferred_model: Optional[str] = None,
    min_ram_gb: Optional[int] = None,
    min_storage_gb: Optional[int] = None,
) -> EquipmentProfileItem:
    return EquipmentProfileItem(
        id="item1",
        profile_id="p1",
        asset_type=asset_type,
        quantity=1,
        preferred_brand=preferred_brand,
        preferred_model=preferred_model,
        min_ram_gb=min_ram_gb,
        min_storage_gb=min_storage_gb,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNoStock:
    def test_no_stock_fallback(self):
        """No in-stock assets -> NO_STOCK_FOR_REQUIRED_TYPE."""
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = []

        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        profile = _profile([_item()])
        result = matcher.match(profile, "c1")

        assert not result.fully_matched
        assert len(result.matched) == 1
        assert (
            result.matched[0].fallback_reason
            == FallbackReason.NO_STOCK_FOR_REQUIRED_TYPE
        )


class TestSpecMismatch:
    def test_spec_mismatch_fallback(self):
        """Candidates fail hard spec filters -> SPEC_MISMATCH."""
        asset = FakeAsset(
            id="a1", notes="4gb ram, 128gb ssd",
        )
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [asset]

        item = _item(min_ram_gb=16)
        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile([item]), "c1")

        assert not result.fully_matched
        assert (
            result.matched[0].fallback_reason
            == FallbackReason.SPEC_MISMATCH
        )


class TestSingleCandidate:
    def test_single_candidate_deterministic(self):
        """Single qualifying candidate -> match without AI."""
        asset = FakeAsset(id="a1")
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [asset]

        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile([_item()]), "c1")

        assert result.fully_matched
        assert result.matched[0].asset_id == "a1"
        assert not result.matched[0].ai_used


class TestMultipleCandidatesAI:
    def test_multiple_candidates_ai_tiebreak(self):
        """Multiple candidates + AI -> AI-chosen asset."""
        a1 = FakeAsset(id="a1", purchase_date=date(2023, 1, 1))
        a2 = FakeAsset(id="a2", purchase_date=date(2024, 1, 1))
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [a1, a2]

        ai = MagicMock()
        ai.select_best_candidate.return_value = "a2"

        matcher = EquipmentProfileMatcher(
            asset_lookup=lookup,
            ai_tiebreaker=ai,
            ai_prompt="pick best",
        )
        result = matcher.match(_profile([_item()]), "c1")

        assert result.fully_matched
        assert result.matched[0].asset_id == "a2"
        assert result.matched[0].ai_used

    def test_ai_unavailable_deterministic_fallback(self):
        """AI returns None -> fallback to oldest purchase_date."""
        a1 = FakeAsset(id="a1", purchase_date=date(2023, 1, 1))
        a2 = FakeAsset(id="a2", purchase_date=date(2024, 1, 1))
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [a1, a2]

        ai = MagicMock()
        ai.select_best_candidate.return_value = None

        matcher = EquipmentProfileMatcher(
            asset_lookup=lookup,
            ai_tiebreaker=ai,
            ai_prompt="pick best",
        )
        result = matcher.match(_profile([_item()]), "c1")

        assert result.fully_matched
        assert result.matched[0].asset_id == "a1"
        assert (
            result.matched[0].fallback_reason
            == FallbackReason.AI_UNAVAILABLE
        )


class TestMultipleCandidatesNoAI:
    def test_no_ai_deterministic(self):
        """Multiple candidates, no AI -> oldest purchase_date."""
        a1 = FakeAsset(id="a1", purchase_date=date(2024, 6, 1))
        a2 = FakeAsset(id="a2", purchase_date=date(2023, 1, 1))
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [a1, a2]

        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile([_item()]), "c1")

        assert result.fully_matched
        assert result.matched[0].asset_id == "a2"


class TestPartialMatch:
    def test_manual_review_partial_match(self):
        """One item matched, one not -> MANUAL_REVIEW_REQUIRED."""
        laptop = FakeAsset(id="a1")
        lookup = MagicMock()

        def side_effect(company_id, asset_type):
            if asset_type == AssetType.LAPTOP.value:
                return [laptop]
            return []  # no monitors

        lookup.find_in_stock_by_type.side_effect = side_effect

        items = [
            _item(AssetType.LAPTOP),
            _item(AssetType.MONITOR),
        ]
        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile(items), "c1")

        assert not result.fully_matched
        assert result.matched[0].asset_id == "a1"
        assert result.matched[1].asset_id is None
        reasons = result.fallback_reasons
        assert (
            FallbackReason.MANUAL_REVIEW_REQUIRED.value
            in reasons
        )


class TestFullMatchAllItems:
    def test_full_match_all_items(self):
        """All items matched -> fully_matched=True."""
        laptop = FakeAsset(id="a1")
        monitor = FakeAsset(id="a2")
        lookup = MagicMock()

        def side_effect(company_id, asset_type):
            if asset_type == AssetType.LAPTOP.value:
                return [laptop]
            if asset_type == AssetType.MONITOR.value:
                return [monitor]
            return []

        lookup.find_in_stock_by_type.side_effect = side_effect

        items = [
            _item(AssetType.LAPTOP),
            _item(AssetType.MONITOR),
        ]
        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile(items), "c1")

        assert result.fully_matched
        assert len(result.matched) == 2
        assert result.matched[0].asset_id == "a1"
        assert result.matched[1].asset_id == "a2"
        assert result.fallback_reasons == []


class TestSoftFilters:
    def test_brand_filter_soft(self):
        """Brand is a soft filter -- keeps all if no match."""
        a1 = FakeAsset(id="a1", brand="HP")
        lookup = MagicMock()
        lookup.find_in_stock_by_type.return_value = [a1]

        item = _item(preferred_brand="Dell")
        matcher = EquipmentProfileMatcher(asset_lookup=lookup)
        result = matcher.match(_profile([item]), "c1")

        # HP asset still matches because brand is soft
        assert result.fully_matched
        assert result.matched[0].asset_id == "a1"
