from unittest.mock import MagicMock, patch

import pytest

from src.auth_bc.user.application.services.google_token_verifier import (
    GoogleEmailNotVerifiedError,
    GoogleTokenVerificationError,
    GoogleTokenVerifier,
)


class TestGoogleTokenVerifier:
    def _mock_response(self, status_code: int, json_data: dict) -> MagicMock:
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data
        return mock

    def test_valid_token_returns_user_info(self):
        verifier = GoogleTokenVerifier(client_id="my-client-id")
        fake_response = self._mock_response(200, {
            "sub": "google_sub_123",
            "email": "user@company.com",
            "name": "Jane Doe",
            "email_verified": True,
        })
        with patch("src.auth_bc.user.application.services.google_token_verifier.requests.get", return_value=fake_response):
            result = verifier.verify("ya29.valid_access_token")

        assert result.sub == "google_sub_123"
        assert result.email == "user@company.com"
        assert result.name == "Jane Doe"
        assert result.email_verified is True

    def test_google_rejects_token_raises_verification_error(self):
        verifier = GoogleTokenVerifier(client_id="my-client-id")
        fake_response = self._mock_response(401, {"error": "invalid_token"})
        with patch("src.auth_bc.user.application.services.google_token_verifier.requests.get", return_value=fake_response):
            with pytest.raises(GoogleTokenVerificationError, match="HTTP 401"):
                verifier.verify("ya29.invalid_token")

    def test_network_error_raises_verification_error(self):
        verifier = GoogleTokenVerifier(client_id="my-client-id")
        with patch(
            "src.auth_bc.user.application.services.google_token_verifier.requests.get",
            side_effect=ConnectionError("timeout"),
        ):
            with pytest.raises(GoogleTokenVerificationError, match="Failed to reach Google"):
                verifier.verify("ya29.any_token")

    def test_unverified_email_raises_error(self):
        verifier = GoogleTokenVerifier(client_id="my-client-id")
        fake_response = self._mock_response(200, {
            "sub": "google_sub_123",
            "email": "user@company.com",
            "name": "Jane Doe",
            "email_verified": False,
        })
        with patch("src.auth_bc.user.application.services.google_token_verifier.requests.get", return_value=fake_response):
            with pytest.raises(GoogleEmailNotVerifiedError):
                verifier.verify("ya29.valid_token")
