"""Tests for OpenAI and Groq request classifier adapters."""

import json
import sys
from unittest.mock import MagicMock, patch

from src.request_bc.request.infrastructure.ai.openai_classifier import (
    OpenAIRequestClassifier,
)
from src.request_bc.request.infrastructure.ai.groq_classifier import (
    GroqRequestClassifier,
)


VALID_TYPES = {
    "incident": [],
    "repair": ["hardware", "software"],
}

MOCK_RESPONSE_JSON = json.dumps({
    "type": "repair",
    "subtype": "hardware",
    "priority_hint": 1,
    "confidence": 0.9,
})


def _mock_openai_response(content: str) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestOpenAIRequestClassifier:
    def test_no_api_key_returns_none(self):
        classifier = OpenAIRequestClassifier(api_key="")
        result = classifier.classify("title", "desc", VALID_TYPES)
        assert result is None

    def test_successful_response(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            MOCK_RESPONSE_JSON
        )

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = OpenAIRequestClassifier(api_key="sk-test")
            result = classifier.classify(
                "Broken laptop", "Screen cracked", VALID_TYPES
            )

        assert result is not None
        assert result.type == "repair"
        assert result.subtype == "hardware"
        assert result.priority_hint == 1
        assert result.confidence == 0.9
        mock_openai.OpenAI.assert_called_once_with(
            api_key="sk-test", timeout=10
        )

    def test_malformed_json_returns_none(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "not valid json"
        )

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = OpenAIRequestClassifier(api_key="sk-test")
            result = classifier.classify("title", "desc", VALID_TYPES)

        assert result is None

    def test_api_error_returns_none(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = RuntimeError("API error")

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = OpenAIRequestClassifier(api_key="sk-test")
            result = classifier.classify("title", "desc", VALID_TYPES)

        assert result is None


class TestGroqRequestClassifier:
    def test_no_api_key_returns_none(self):
        classifier = GroqRequestClassifier(api_key="")
        result = classifier.classify("title", "desc", VALID_TYPES)
        assert result is None

    def test_successful_response(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            MOCK_RESPONSE_JSON
        )

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = GroqRequestClassifier(api_key="gsk-test")
            result = classifier.classify(
                "Broken laptop", "Screen cracked", VALID_TYPES
            )

        assert result is not None
        assert result.type == "repair"
        assert result.subtype == "hardware"
        assert result.priority_hint == 1
        assert result.confidence == 0.9
        mock_openai.OpenAI.assert_called_once_with(
            api_key="gsk-test",
            base_url="https://api.groq.com/openai/v1",
            timeout=10,
        )

    def test_malformed_json_returns_none(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "not valid json"
        )

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = GroqRequestClassifier(api_key="gsk-test")
            result = classifier.classify("title", "desc", VALID_TYPES)

        assert result is None

    def test_api_error_returns_none(self):
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = RuntimeError("API error")

        with patch.dict(sys.modules, {"openai": mock_openai}):
            classifier = GroqRequestClassifier(api_key="gsk-test")
            result = classifier.classify("title", "desc", VALID_TYPES)

        assert result is None
