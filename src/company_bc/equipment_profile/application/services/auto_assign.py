import logging
from typing import Any, Optional

from src.company_bc.assignment_config.domain.enums import (
    AIProvider,
    FallbackReason,
)
from src.company_bc.equipment_profile.application.services.ai_tiebreaker import (  # noqa: E501
    AITieBreakerPort,
    GroqAdapter,
    OpenAIAdapter,
)
from src.company_bc.equipment_profile.application.services.matching import (  # noqa: E501
    EquipmentProfileMatcher,
    MatchResult,
)

logger = logging.getLogger(__name__)


class AutoAssignService:
    """Orchestrate profile matching and assignment."""

    def __init__(
        self,
        profile_repo: Any,
        config_repo: Any,
        asset_lookup: Any,
        ai_settings: Any,
    ):
        self.profile_repo = profile_repo
        self.config_repo = config_repo
        self.asset_lookup = asset_lookup
        self.ai_settings = ai_settings

    def attempt_assignment(
        self,
        company_id: str,
        department_id: Optional[str],
        employee_role_id: Optional[str],
    ) -> dict:
        """Attempt auto-assignment. Returns metadata."""
        if not department_id or not employee_role_id:
            return {
                "status": "skipped",
                "reason": "no_department_or_role",
            }

        # Find active profile
        profile = self.profile_repo.find_active(
            company_id=company_id,
            department_id=department_id,
            employee_role_id=employee_role_id,
        )
        if not profile:
            return {
                "status": "fallback",
                "reasons": [
                    FallbackReason.NO_ACTIVE_PROFILE.value,
                ],
            }

        # Build AI tiebreaker if configured
        ai_tiebreaker = self._build_ai_tiebreaker(
            company_id,
        )
        ai_prompt = ""
        config = self.config_repo.find_by_company(
            company_id,
        )
        if config:
            ai_prompt = config.prompt_template

        matcher = EquipmentProfileMatcher(
            asset_lookup=self.asset_lookup,
            ai_tiebreaker=ai_tiebreaker,
            ai_prompt=ai_prompt,
        )
        result = matcher.match(profile, company_id)

        return self._build_metadata(result)

    def _build_ai_tiebreaker(
        self, company_id: str,
    ) -> Optional[AITieBreakerPort]:
        config = self.config_repo.find_by_company(
            company_id,
        )
        if not config:
            return None

        if config.provider == AIProvider.OPENAI:
            key = self.ai_settings.OPENAI_API_KEY
            if key:
                return OpenAIAdapter(api_key=key)
        elif config.provider == AIProvider.GROQ:
            key = self.ai_settings.GROQ_API_KEY
            if key:
                return GroqAdapter(api_key=key)
        return None

    @staticmethod
    def _build_metadata(
        result: MatchResult,
    ) -> dict:
        matched_assets = [
            {
                "asset_type": m.item.asset_type,
                "asset_id": m.asset_id,
                "ai_used": m.ai_used,
            }
            for m in result.matched
            if m.asset_id
        ]
        return {
            "status": "matched"
            if result.fully_matched
            else "partial",
            "profile_id": result.profile_id,
            "matched_assets": matched_assets,
            "fallback_reasons": result.fallback_reasons,
        }
