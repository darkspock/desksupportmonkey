"""Tests for ClassificationOrchestrator and ClassificationResult."""

from unittest.mock import MagicMock

from src.request_bc.request.application.services.request_classifier import (
    ClassificationOrchestrator,
    ClassificationResult,
)


VALID_TYPES = {
    "incident": [],
    "repair": ["hardware", "software", "network"],
    "new_equipment": ["computer", "mobile", "peripheral"],
    "configuration": ["software_install", "account_setup"],
}


class TestClassificationResult:
    def test_fields(self):
        result = ClassificationResult(
            type="incident",
            subtype=None,
            priority_hint=1,
            confidence=0.85,
        )
        assert result.type == "incident"
        assert result.subtype is None
        assert result.priority_hint == 1
        assert result.confidence == 0.85

    def test_frozen(self):
        result = ClassificationResult(
            type="incident", subtype=None, priority_hint=0, confidence=0.9
        )
        try:
            result.type = "repair"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestClassificationOrchestrator:
    def setup_method(self):
        self.classifier = MagicMock()
        self.orchestrator = ClassificationOrchestrator(self.classifier)

    def test_successful_classification(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="repair", subtype="hardware", priority_hint=1, confidence=0.9
        )
        result = self.orchestrator.classify(
            "Broken laptop", "Screen is cracked", VALID_TYPES
        )
        assert result is not None
        assert result.type == "repair"
        assert result.subtype == "hardware"
        assert result.priority_hint == 1
        assert result.confidence == 0.9

    def test_invalid_type_returns_none(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="unknown_type", subtype=None, priority_hint=0, confidence=0.8
        )
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is None

    def test_invalid_subtype_for_type_returns_none(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="repair", subtype="nonexistent", priority_hint=0, confidence=0.8
        )
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is None

    def test_subtype_for_empty_subtypes_type_returns_none(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="incident", subtype="hardware", priority_hint=0, confidence=0.8
        )
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is None

    def test_classifier_exception_returns_none(self):
        self.classifier.classify.side_effect = RuntimeError("API down")
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is None

    def test_classifier_returns_none(self):
        self.classifier.classify.return_value = None
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is None

    def test_valid_type_with_none_subtype_accepted(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="repair", subtype=None, priority_hint=-1, confidence=0.7
        )
        result = self.orchestrator.classify(
            "Something", "Some description", VALID_TYPES
        )
        assert result is not None
        assert result.subtype is None
        assert result.priority_hint == -1

    def test_custom_instructions_passed_through(self):
        self.classifier.classify.return_value = ClassificationResult(
            type="incident", subtype=None, priority_hint=0, confidence=0.95
        )
        result = self.orchestrator.classify(
            "Title", "Desc", VALID_TYPES, custom_instructions="Be strict"
        )
        assert result is not None
        self.classifier.classify.assert_called_once_with(
            "Title", "Desc", VALID_TYPES, "Be strict"
        )
