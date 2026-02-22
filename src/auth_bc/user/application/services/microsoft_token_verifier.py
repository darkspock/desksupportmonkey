import logging
from dataclasses import dataclass

import jwt
import requests

logger = logging.getLogger(__name__)

_JWKS_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
_OIDC_ISSUER_TEMPLATE = "https://login.microsoftonline.com/{tenant}/v2.0"
_OIDC_ISSUER_COMMON = "https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0"


class MicrosoftTokenVerificationError(Exception):
    pass


class MicrosoftEmailNotVerifiedError(Exception):
    pass


class MicrosoftMissingEmailError(Exception):
    pass


@dataclass
class MicrosoftUserInfo:
    oid: str
    email: str
    name: str | None


class MicrosoftTokenVerifier:
    def __init__(self, client_id: str, tenant_id: str = "common"):
        self._client_id = client_id
        self._tenant_id = tenant_id

    def verify(self, id_token_str: str) -> MicrosoftUserInfo:
        try:
            unverified_header = jwt.get_unverified_header(id_token_str)
            kid = unverified_header.get("kid")
        except Exception as exc:
            raise MicrosoftTokenVerificationError(f"Invalid token header: {exc}") from exc

        jwks = self._fetch_jwks()
        public_key = self._find_key(jwks, kid)

        # Build the list of valid issuers
        if self._tenant_id == "common":
            issuer = None  # skip issuer check for multi-tenant
        else:
            issuer = _OIDC_ISSUER_TEMPLATE.format(tenant=self._tenant_id)

        try:
            options: dict = {"verify_exp": True}
            if issuer is None:
                options["verify_iss"] = False

            payload = jwt.decode(
                id_token_str,
                public_key,
                algorithms=["RS256"],
                audience=self._client_id,
                options=options,
            )
        except jwt.ExpiredSignatureError as exc:
            raise MicrosoftTokenVerificationError("Token has expired") from exc
        except Exception as exc:
            raise MicrosoftTokenVerificationError(str(exc)) from exc

        email = payload.get("email") or payload.get("upn") or payload.get("preferred_username")
        if not email:
            raise MicrosoftMissingEmailError("Token does not contain an email claim")

        # Microsoft does not include email_verified; email from Azure AD is verified by default
        oid = payload.get("oid") or payload.get("sub")
        name = payload.get("name")

        return MicrosoftUserInfo(oid=oid, email=email, name=name)

    def _fetch_jwks(self) -> dict:
        url = _JWKS_URL_TEMPLATE.format(tenant=self._tenant_id)
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise MicrosoftTokenVerificationError(f"Failed to fetch JWKS: {exc}") from exc

    def _find_key(self, jwks: dict, kid: str | None) -> object:
        keys = jwks.get("keys", [])
        for key in keys:
            if kid is None or key.get("kid") == kid:
                try:
                    return jwt.algorithms.RSAAlgorithm.from_jwk(key)
                except Exception as exc:
                    logger.debug("Could not parse JWK: %s", exc)
        raise MicrosoftTokenVerificationError(f"No matching key found for kid={kid}")
