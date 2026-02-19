import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AITieBreakerPort(ABC):
    """Port for AI-based asset selection."""

    @abstractmethod
    def select_best_candidate(
        self,
        candidates: list[Any],
        profile_item_desc: str,
        prompt: str,
    ) -> Optional[str]:
        """Return asset_id of best candidate, or None."""
        ...  # pragma: no cover


class OpenAIAdapter(AITieBreakerPort):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def select_best_candidate(
        self,
        candidates: list[Any],
        profile_item_desc: str,
        prompt: str,
    ) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            assets_desc = json.dumps(
                [
                    {
                        "id": c.id,
                        "brand": c.brand,
                        "model": c.model,
                        "purchase_date": str(
                            c.purchase_date
                        )
                        if c.purchase_date
                        else None,
                        "notes": c.notes,
                    }
                    for c in candidates
                ]
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Profile requirement: "
                            f"{profile_item_desc}\n"
                            f"Candidates: {assets_desc}\n"
                            f"Return ONLY the asset id."
                        ),
                    },
                ],
                max_tokens=50,
            )
            chosen = resp.choices[0].message.content
            if not isinstance(chosen, str):
                return None
            chosen = chosen.strip().strip('"').strip("'")
            ids = {c.id for c in candidates}
            if chosen in ids:
                return chosen
            return None
        except Exception as e:
            logger.warning("OpenAI tie-break failed: %s", e)
            return None


class GroqAdapter(AITieBreakerPort):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def select_best_candidate(
        self,
        candidates: list[Any],
        profile_item_desc: str,
        prompt: str,
    ) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            import openai

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            assets_desc = json.dumps(
                [
                    {
                        "id": c.id,
                        "brand": c.brand,
                        "model": c.model,
                        "purchase_date": str(
                            c.purchase_date
                        )
                        if c.purchase_date
                        else None,
                        "notes": c.notes,
                    }
                    for c in candidates
                ]
            )
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Profile requirement: "
                            f"{profile_item_desc}\n"
                            f"Candidates: {assets_desc}\n"
                            f"Return ONLY the asset id."
                        ),
                    },
                ],
                max_tokens=50,
            )
            chosen = resp.choices[0].message.content
            if not isinstance(chosen, str):
                return None
            chosen = chosen.strip().strip('"').strip("'")
            ids = {c.id for c in candidates}
            if chosen in ids:
                return chosen
            return None
        except Exception as e:
            logger.warning("Groq tie-break failed: %s", e)
            return None


def deterministic_fallback(
    candidates: list[Any],
) -> Optional[str]:
    """Pick the asset with the oldest purchase_date."""
    dated = [
        c for c in candidates if c.purchase_date
    ]
    if dated:
        dated.sort(key=lambda c: c.purchase_date)
        chosen = dated[0].id
        return chosen if isinstance(chosen, str) else None
    if not candidates:
        return None
    chosen = candidates[0].id
    return chosen if isinstance(chosen, str) else None
