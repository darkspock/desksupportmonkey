from dataclasses import dataclass

import requests  # type: ignore[import-untyped]


class GoogleTokenVerificationError(Exception):
    pass


class GoogleEmailNotVerifiedError(Exception):
    pass


@dataclass
class GoogleUserInfo:
    sub: str
    email: str
    name: str | None
    email_verified: bool


class GoogleTokenVerifier:
    _USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, client_id: str):
        self._client_id = client_id

    def verify(self, access_token: str) -> GoogleUserInfo:
        try:
            response = requests.get(
                self._USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5,
            )
        except Exception as exc:
            raise GoogleTokenVerificationError(f"Failed to reach Google: {exc}") from exc

        if response.status_code != 200:
            raise GoogleTokenVerificationError(f"Google rejected token (HTTP {response.status_code})")

        info = response.json()

        if not info.get("email_verified"):
            raise GoogleEmailNotVerifiedError("Google account email is not verified")

        email = info.get("email")
        if not email:
            raise GoogleTokenVerificationError("No email in Google userinfo response")

        return GoogleUserInfo(
            sub=info["sub"],
            email=email,
            name=info.get("name"),
            email_verified=bool(info.get("email_verified")),
        )
