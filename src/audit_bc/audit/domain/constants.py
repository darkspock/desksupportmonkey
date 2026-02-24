from copy import deepcopy
from typing import Optional


SANITIZED_FIELDS: set[str] = {
    "password",
    "password_hash",
    "token",
    "magic_link",
    "secret",
    "stripe_secret_key",
    "credentials",
    "current_password",
    "new_password",
}


def sanitize_request_data(data: Optional[dict]) -> Optional[dict]:
    """Recursively redact sensitive fields from request data."""
    if data is None:
        return None
    result = deepcopy(data)
    _redact(result)
    return result


def _redact(obj: dict) -> None:
    for key in list(obj.keys()):
        if key in SANITIZED_FIELDS:
            obj[key] = "[REDACTED]"
        elif isinstance(obj[key], dict):
            _redact(obj[key])
