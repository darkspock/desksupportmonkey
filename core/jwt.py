import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from core.config import settings

logger = logging.getLogger(__name__)


class InvalidTokenError(Exception):
    pass


class ExpiredTokenError(Exception):
    pass


class JWTService:
    def __init__(
        self,
        secret: str = settings.auth.SECRET_KEY,
        algorithm: str = settings.auth.ALGORITHM,
        expire_hours: int = 24,
    ):
        self.secret = secret
        self.algorithm = algorithm
        self.expire_hours = expire_hours

    def create_token(
        self,
        user_id: str,
        company_id: Optional[str],
        role: str,
    ) -> str:
        payload = {
            "sub": user_id,
            "company_id": company_id,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.expire_hours),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
