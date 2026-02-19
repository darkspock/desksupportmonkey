import logging
from dataclasses import dataclass
from typing import Optional

from src.request_bc.request.application.ports import RequestClassifierPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    type: str
    subtype: Optional[str]
    priority_hint: int  # -1 to +2
    confidence: float  # 0.0 to 1.0


class ClassificationOrchestrator:
    def __init__(self, classifier: RequestClassifierPort):
        self.classifier = classifier

    def classify(
        self,
        title: str,
        description: str,
        valid_types: dict[str, list[str]],
        custom_instructions: Optional[str] = None,
    ) -> Optional[ClassificationResult]:
        """Call the classifier and validate the result.

        Returns None if:
        - Classifier raises any exception
        - Returned type is not in valid_types
        - Returned subtype is not valid for the type
        - Type has empty subtypes list but AI suggested a subtype
        """
        try:
            result = self.classifier.classify(
                title, description, valid_types, custom_instructions
            )
            if result is None:
                return None

            if result.type not in valid_types:
                logger.warning("AI returned invalid type: %s", result.type)
                return None

            allowed_subtypes = valid_types[result.type]

            if not allowed_subtypes:
                if result.subtype is not None:
                    logger.warning(
                        "AI returned subtype %s for type %s which has no subtypes",
                        result.subtype,
                        result.type,
                    )
                    return None
            else:
                if result.subtype is not None and result.subtype not in allowed_subtypes:
                    logger.warning(
                        "AI returned invalid subtype %s for type %s",
                        result.subtype,
                        result.type,
                    )
                    return None

            return result
        except Exception:
            logger.warning("Classification failed", exc_info=True)
            return None
