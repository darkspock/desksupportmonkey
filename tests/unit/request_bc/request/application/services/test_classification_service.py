from unittest.mock import MagicMock, patch

import pytest

from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)
from src.request_bc.request.application.services.classification_service import (
    ClassificationService,
    ClassificationServiceResult,
)
from src.request_bc.request.application.services.request_classifier import (
    ClassificationResult,
)


VALID_TYPES = {
    "incident": [],
    "new_equipment": ["computer", "mobile", "peripheral", "monitor", "software_license"],
    "repair": ["hardware", "software", "network", "security", "other"],
    "configuration": ["software_install", "account_setup", "permissions"],
    "access_request": ["system_access", "physical_access", "vpn"],
    "onboarding": [],
}


def _make_config(**overrides):
    defaults = dict(
        company_id="comp1",
        is_enabled=True,
        provider=AIProvider.OPENAI,
        model="gpt-4o-mini",
        confidence_threshold=0.7,
        prompt_template="Classify this request",
        timeout_seconds=5,
    )
    defaults.update(overrides)
    return CompanyClassificationConfig.create(**defaults)


def _make_classifier_mock(result):
    """Return a mock RequestClassifierPort whose classify() returns `result`."""
    mock = MagicMock()
    mock.classify.return_value = result
    return mock


class TestClassificationServiceOverride:
    def test_confident_type_differs_override_applied(self):
        ai_result = ClassificationResult(
            type="configuration", subtype="account_setup",
            priority_hint=1, confidence=0.9,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("Setup email", "Need email configured", "incident", None)

        assert result.resolved_type == "configuration"
        assert result.resolved_subtype == "account_setup"
        assert result.ai_priority_hint == 1
        assert result.ai_classification["override_applied"] is True
        assert result.ai_classification["user_original"] == {"type": "incident", "subtype": None}

    def test_confident_same_type_no_override(self):
        ai_result = ClassificationResult(
            type="incident", subtype=None,
            priority_hint=0, confidence=0.95,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("System down", "Cannot login", "incident", None)

        assert result.resolved_type == "incident"
        assert result.resolved_subtype is None
        assert result.ai_classification["ai_used"] is True
        assert result.ai_classification["override_applied"] is False
        assert "user_original" not in result.ai_classification

    def test_below_threshold_no_override(self):
        ai_result = ClassificationResult(
            type="configuration", subtype="account_setup",
            priority_hint=1, confidence=0.5,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("Setup email", "Need email configured", "incident", None)

        assert result.resolved_type == "incident"  # user's original
        assert result.resolved_subtype is None
        assert result.ai_classification["override_applied"] is False

    def test_classifier_returns_none_fallback(self):
        classifier = _make_classifier_mock(None)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("System down", "Cannot login", "incident", None)

        assert result.resolved_type == "incident"
        assert result.ai_priority_hint == 0
        assert result.ai_classification == {"ai_used": False}

    def test_invalid_type_suggestion_no_override(self):
        """Orchestrator filters invalid types → returns None → fallback."""
        ai_result = ClassificationResult(
            type="invalid_type", subtype=None,
            priority_hint=1, confidence=0.95,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("System down", "Cannot login", "incident", None)

        # Orchestrator returns None for invalid type → fallback
        assert result.resolved_type == "incident"
        assert result.ai_classification["ai_used"] is False

    def test_invalid_subtype_suggestion_no_override(self):
        """Orchestrator filters invalid subtypes → returns None → fallback."""
        ai_result = ClassificationResult(
            type="repair", subtype="vpn",  # vpn is not valid for repair
            priority_hint=0, confidence=0.95,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("Broken keyboard", "Keys stuck", "repair", "hardware")

        # Orchestrator returns None for invalid subtype → fallback
        assert result.resolved_type == "repair"
        assert result.resolved_subtype == "hardware"
        assert result.ai_classification["ai_used"] is False

    def test_latency_recorded_in_metadata(self):
        ai_result = ClassificationResult(
            type="incident", subtype=None,
            priority_hint=0, confidence=0.9,
        )
        classifier = _make_classifier_mock(ai_result)
        config = _make_config(confidence_threshold=0.7)

        svc = ClassificationService(classifier, config, VALID_TYPES)
        result = svc.classify_request("System down", "Cannot login", "incident", None)

        assert "latency_ms" in result.ai_classification
        assert isinstance(result.ai_classification["latency_ms"], int)
        assert result.ai_classification["latency_ms"] >= 0


class TestBuildClassifier:
    def test_build_openai_classifier(self):
        config = _make_config(provider=AIProvider.OPENAI, model="gpt-4o-mini", timeout_seconds=5)
        ai_settings = MagicMock()
        ai_settings.OPENAI_API_KEY = "sk-test-key"

        classifier = ClassificationService.build_classifier(config, ai_settings)

        from src.request_bc.request.infrastructure.ai.openai_classifier import (
            OpenAIRequestClassifier,
        )
        assert isinstance(classifier, OpenAIRequestClassifier)

    def test_build_groq_classifier(self):
        config = _make_config(provider=AIProvider.GROQ, model="llama-3.1-8b-instant", timeout_seconds=5)
        ai_settings = MagicMock()
        ai_settings.GROQ_API_KEY = "gsk-test-key"

        classifier = ClassificationService.build_classifier(config, ai_settings)

        from src.request_bc.request.infrastructure.ai.groq_classifier import (
            GroqRequestClassifier,
        )
        assert isinstance(classifier, GroqRequestClassifier)
