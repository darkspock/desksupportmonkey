import json
from unittest.mock import MagicMock, patch

import pytest

from src.auth_bc.user.application.services.microsoft_token_verifier import (
    MicrosoftMissingEmailError,
    MicrosoftTokenVerificationError,
    MicrosoftTokenVerifier,
    MicrosoftUserInfo,
)


def _fake_header():
    return {"kid": "test_kid", "alg": "RS256"}


def _valid_payload():
    return {
        "oid": "ms_oid_123",
        "email": "user@company.com",
        "name": "Jane Doe",
    }


class TestMicrosoftTokenVerifier:
    def test_valid_token_returns_user_info(self):
        verifier = MicrosoftTokenVerifier(client_id="my-client-id", tenant_id="my-tenant")
        fake_key = MagicMock()
        mock_jwks = {"keys": [{"kid": "test_kid", "kty": "RSA", "n": "x", "e": "y"}]}

        with patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.get_unverified_header",
            return_value=_fake_header(),
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.MicrosoftTokenVerifier._fetch_jwks",
            return_value=mock_jwks,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.algorithms.RSAAlgorithm.from_jwk",
            return_value=fake_key,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.decode",
            return_value=_valid_payload(),
        ):
            result = verifier.verify("valid_id_token")

        assert result.oid == "ms_oid_123"
        assert result.email == "user@company.com"
        assert result.name == "Jane Doe"

    def test_expired_token_raises_verification_error(self):
        import jwt as jwt_lib

        verifier = MicrosoftTokenVerifier(client_id="my-client-id")
        fake_key = MagicMock()
        mock_jwks = {"keys": [{"kid": "test_kid"}]}

        with patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.get_unverified_header",
            return_value=_fake_header(),
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.MicrosoftTokenVerifier._fetch_jwks",
            return_value=mock_jwks,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.algorithms.RSAAlgorithm.from_jwk",
            return_value=fake_key,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.decode",
            side_effect=jwt_lib.ExpiredSignatureError("Token expired"),
        ):
            with pytest.raises(MicrosoftTokenVerificationError, match="expired"):
                verifier.verify("expired_token")

    def test_missing_email_raises_error(self):
        verifier = MicrosoftTokenVerifier(client_id="my-client-id")
        fake_key = MagicMock()
        mock_jwks = {"keys": [{"kid": "test_kid"}]}
        payload_no_email = {"oid": "ms_oid_123", "name": "No Email"}

        with patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.get_unverified_header",
            return_value=_fake_header(),
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.MicrosoftTokenVerifier._fetch_jwks",
            return_value=mock_jwks,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.algorithms.RSAAlgorithm.from_jwk",
            return_value=fake_key,
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.decode",
            return_value=payload_no_email,
        ):
            with pytest.raises(MicrosoftMissingEmailError):
                verifier.verify("token_without_email")

    def test_jwks_fetch_failure_raises_error(self):
        verifier = MicrosoftTokenVerifier(client_id="my-client-id")

        with patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.jwt.get_unverified_header",
            return_value=_fake_header(),
        ), patch(
            "src.auth_bc.user.application.services.microsoft_token_verifier.MicrosoftTokenVerifier._fetch_jwks",
            side_effect=MicrosoftTokenVerificationError("Failed to fetch JWKS"),
        ):
            with pytest.raises(MicrosoftTokenVerificationError, match="JWKS"):
                verifier.verify("any_token")
