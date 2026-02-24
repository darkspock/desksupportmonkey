import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from src.company_bc.assignment_config.domain.enums import (
    FallbackReason,
)
from src.company_bc.equipment_profile.application.services.ai_tiebreaker import (  # noqa: E501
    AITieBreakerPort,
    deterministic_fallback,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
    EquipmentProfileItem,
)

logger = logging.getLogger(__name__)


@dataclass
class ItemMatchResult:
    item: EquipmentProfileItem
    asset_id: Optional[str] = None
    fallback_reason: Optional[FallbackReason] = None
    ai_used: bool = False


@dataclass
class MatchResult:
    profile_id: str
    matched: list[ItemMatchResult] = field(
        default_factory=list,
    )
    fallback_reasons: list[str] = field(
        default_factory=list,
    )
    fully_matched: bool = False


class EquipmentProfileMatcher:
    """Deterministic matching engine with AI tie-break."""

    def __init__(
        self,
        asset_lookup: Any,
        ai_tiebreaker: Optional[AITieBreakerPort] = None,
        ai_prompt: str = "",
    ):
        self.asset_lookup = asset_lookup
        self.ai_tiebreaker = ai_tiebreaker
        self.ai_prompt = ai_prompt

    def match(
        self,
        profile: EquipmentProfile,
        company_id: str,
    ) -> MatchResult:
        result = MatchResult(profile_id=profile.id)

        for item in profile.items:
            item_result = self._match_item(
                item, company_id,
            )
            result.matched.append(item_result)
            if item_result.fallback_reason:
                result.fallback_reasons.append(
                    item_result.fallback_reason.value,
                )

        result.fully_matched = all(
            m.asset_id is not None
            for m in result.matched
        )
        if (
            not result.fully_matched
            and result.matched
        ):
            has_partial = any(
                m.asset_id is not None
                for m in result.matched
            )
            if has_partial:
                reason = (
                    FallbackReason.MANUAL_REVIEW_REQUIRED
                )
                result.fallback_reasons.append(
                    reason.value,
                )

        return result

    def _match_item(
        self,
        item: EquipmentProfileItem,
        company_id: str,
    ) -> ItemMatchResult:
        # Step 1: Find in-stock assets by type
        candidates = (
            self.asset_lookup.find_in_stock_by_type(
                company_id=company_id,
                asset_type=item.asset_type,
            )
        )
        if not candidates:
            return ItemMatchResult(
                item=item,
                fallback_reason=(
                    FallbackReason.NO_STOCK_FOR_REQUIRED_TYPE
                ),
            )

        # Step 2: Apply spec filters
        filtered = self._apply_spec_filters(
            candidates, item,
        )
        if not filtered:
            return ItemMatchResult(
                item=item,
                fallback_reason=(
                    FallbackReason.SPEC_MISMATCH
                ),
            )

        # Step 3: Single candidate → deterministic
        if len(filtered) == 1:
            return ItemMatchResult(
                item=item,
                asset_id=filtered[0].id,
            )

        # Step 4: Multiple → AI tie-break
        if self.ai_tiebreaker and self.ai_prompt:
            desc = self._item_description(item)
            chosen = (
                self.ai_tiebreaker
                .select_best_candidate(
                    filtered, desc, self.ai_prompt,
                )
            )
            if chosen:
                return ItemMatchResult(
                    item=item,
                    asset_id=chosen,
                    ai_used=True,
                )
            # AI failed → deterministic fallback
            fallback_id = deterministic_fallback(
                filtered,
            )
            return ItemMatchResult(
                item=item,
                asset_id=fallback_id,
                fallback_reason=(
                    FallbackReason.AI_UNAVAILABLE
                ),
            )

        # No AI → deterministic
        fallback_id = deterministic_fallback(filtered)
        return ItemMatchResult(
            item=item,
            asset_id=fallback_id,
        )

    def _apply_spec_filters(
        self,
        candidates: list[Any],
        item: EquipmentProfileItem,
    ) -> list[Any]:
        result = list(candidates)

        # Brand/model are soft filters
        if item.preferred_brand:
            branded = [
                c
                for c in result
                if c.brand
                and c.brand.lower()
                == item.preferred_brand.lower()
            ]
            if branded:
                result = branded

        if item.preferred_model:
            modeled = [
                c
                for c in result
                if c.model
                and c.model.lower()
                == item.preferred_model.lower()
            ]
            if modeled:
                result = modeled

        # RAM/storage are hard filters (from notes)
        if item.min_ram_gb:
            result = [
                c
                for c in result
                if self._check_ram(c, item.min_ram_gb)
            ]

        if item.min_storage_gb:
            result = [
                c
                for c in result
                if self._check_storage(
                    c, item.min_storage_gb,
                )
            ]

        return result

    @staticmethod
    def _check_ram(
        asset: Any, min_gb: int,
    ) -> bool:
        """Check RAM from notes field (best-effort)."""
        if not asset.notes:
            return True  # No info = pass
        notes = asset.notes.lower()
        import re

        match = re.search(r'(\d+)\s*gb\s*ram', notes)
        if match:
            return int(match.group(1)) >= min_gb
        return True  # No parseable info = pass

    @staticmethod
    def _check_storage(
        asset: Any, min_gb: int,
    ) -> bool:
        """Check storage from notes field."""
        if not asset.notes:
            return True
        notes = asset.notes.lower()
        import re

        match = re.search(
            r'(\d+)\s*(?:gb|tb)\s*(?:ssd|hdd|storage|disk)',
            notes,
        )
        if match:
            val = int(match.group(1))
            if 'tb' in notes[
                match.start():match.end()
            ]:
                val *= 1024
            return val >= min_gb
        return True

    @staticmethod
    def _item_description(
        item: EquipmentProfileItem,
    ) -> str:
        parts = [f"type={item.asset_type}"]
        if item.preferred_brand:
            parts.append(
                f"brand={item.preferred_brand}",
            )
        if item.preferred_model:
            parts.append(
                f"model={item.preferred_model}",
            )
        if item.min_ram_gb:
            parts.append(
                f"min_ram={item.min_ram_gb}GB",
            )
        if item.min_storage_gb:
            parts.append(
                f"min_storage={item.min_storage_gb}GB",
            )
        return ", ".join(parts)
