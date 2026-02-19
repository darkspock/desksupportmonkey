import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)
from src.request_bc.request.application.ports import RequestClassifierPort
from src.request_bc.request.application.services.request_classifier import (
    ClassificationOrchestrator,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationServiceResult:
    resolved_type: str
    resolved_subtype: Optional[str]
    ai_priority_hint: int
    ai_classification: Optional[dict[str, Any]]


class ClassificationService:
    def __init__(
        self,
        classifier: RequestClassifierPort,
        config: CompanyClassificationConfig,
        valid_types: dict[str, list[str]],
    ):
        self.orchestrator = ClassificationOrchestrator(classifier)
        self.config = config
        self.valid_types = valid_types

    def classify_request(
        self,
        title: str,
        description: str,
        user_type: str,
        user_subtype: Optional[str],
    ) -> ClassificationServiceResult:
        start = time.time()
        result = self.orchestrator.classify(
            title,
            description,
            self.valid_types,
            self.config.prompt_template,
        )
        latency_ms = int((time.time() - start) * 1000)

        if result is None:
            return ClassificationServiceResult(
                resolved_type=user_type,
                resolved_subtype=user_subtype,
                ai_priority_hint=0,
                ai_classification={"ai_used": False},
            )

        override_applied = False
        user_original = None
        resolved_type = user_type
        resolved_subtype = user_subtype

        type_differs = result.type != user_type
        subtype_differs = result.subtype != user_subtype
        confident = result.confidence >= self.config.confidence_threshold

        if confident and (type_differs or subtype_differs):
            resolved_type = result.type
            resolved_subtype = result.subtype
            override_applied = True
            user_original = {"type": user_type, "subtype": user_subtype}

        metadata: dict[str, Any] = {
            "ai_used": True,
            "provider": self.config.provider.value,
            "model": self.config.model,
            "confidence": result.confidence,
            "suggested_type": result.type,
            "suggested_subtype": result.subtype,
            "priority_hint": result.priority_hint,
            "override_applied": override_applied,
            "latency_ms": latency_ms,
        }
        if user_original is not None:
            metadata["user_original"] = user_original

        return ClassificationServiceResult(
            resolved_type=resolved_type,
            resolved_subtype=resolved_subtype,
            ai_priority_hint=result.priority_hint,
            ai_classification=metadata,
        )

    @staticmethod
    def build_classifier(
        config: CompanyClassificationConfig,
        ai_settings: Any,
    ) -> Optional[RequestClassifierPort]:
        from src.request_bc.request.infrastructure.ai.groq_classifier import (
            GroqRequestClassifier,
        )
        from src.request_bc.request.infrastructure.ai.openai_classifier import (
            OpenAIRequestClassifier,
        )

        model = config.model or None
        timeout = config.timeout_seconds
        logger.warning(
            "AI_TRACE build_classifier: provider=%s model=%s timeout_seconds=%s",
            config.provider.value,
            config.model,
            timeout,
        )

        if config.provider == AIProvider.OPENAI:
            api_key = ai_settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("AI_TRACE build_classifier skipped: missing OPENAI_API_KEY")
                return None
            logger.warning("AI_TRACE build_classifier selected OpenAIRequestClassifier")
            return OpenAIRequestClassifier(
                api_key=api_key,
                **({"model": model} if model else {}),
                timeout_seconds=timeout,
            )
        elif config.provider == AIProvider.GROQ:
            api_key = ai_settings.GROQ_API_KEY
            if not api_key:
                logger.warning("AI_TRACE build_classifier skipped: missing GROQ_API_KEY")
                return None
            logger.warning("AI_TRACE build_classifier selected GroqRequestClassifier")
            return GroqRequestClassifier(
                api_key=api_key,
                **({"model": model} if model else {}),
                timeout_seconds=timeout,
            )
        logger.warning(
            "AI_TRACE build_classifier skipped: unsupported provider=%s",
            config.provider.value,
        )
        return None
