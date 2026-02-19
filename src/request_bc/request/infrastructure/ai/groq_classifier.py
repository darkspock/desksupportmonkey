import json
import logging
from typing import Optional

from src.request_bc.request.application.ports import RequestClassifierPort
from src.request_bc.request.application.services.request_classifier import (
    ClassificationResult,
)

logger = logging.getLogger(__name__)


class GroqRequestClassifier(RequestClassifierPort):
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        timeout_seconds: int = 10,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def classify(
        self,
        title: str,
        description: str,
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> Optional[ClassificationResult]:
        if not self.api_key:
            logger.warning("AI_TRACE groq classify skipped: missing api key")
            return None
        try:
            import openai

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=self.timeout_seconds,
            )

            system_content = self._build_system_message(
                valid_types, custom_instructions
            )
            user_content = f"Title: {title}\nDescription: {description}"
            logger.warning(
                "AI_TRACE groq request start: model=%s timeout_seconds=%s "
                "title_len=%s description_len=%s",
                self.model,
                self.timeout_seconds,
                len(title),
                len(description),
            )

            resp = client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=200,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
            )

            raw = resp.choices[0].message.content or ""
            data = json.loads(raw)
            logger.warning(
                "AI_TRACE groq request success: type=%s subtype=%s priority_hint=%s confidence=%s",
                data.get("type"),
                data.get("subtype"),
                data.get("priority_hint"),
                data.get("confidence"),
            )

            return ClassificationResult(
                type=data["type"],
                subtype=data.get("subtype"),
                priority_hint=int(data.get("priority_hint", 0)),
                confidence=float(data.get("confidence", 0.0)),
            )
        except Exception as e:
            logger.warning("AI_TRACE groq classify failed: %s", e)
            return None

    @staticmethod
    def _build_system_message(
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> str:
        types_schema = json.dumps(valid_types, indent=2)
        parts = [
            "You are a request classifier for an IT service desk.",
            f"Valid types and subtypes:\n{types_schema}",
            (
                "Respond with JSON: "
                '{"type": "...", "subtype": "..." or null, '
                '"priority_hint": N, "confidence": 0.XX}'
            ),
            (
                "priority_hint guide: "
                "-1 = lower priority, 0 = normal, "
                "+1 = somewhat urgent, +2 = critical/emergency"
            ),
        ]
        if custom_instructions:
            parts.append(f"Additional instructions:\n{custom_instructions}")
        return "\n\n".join(parts)
