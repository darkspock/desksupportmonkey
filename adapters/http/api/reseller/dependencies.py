from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.containers.reseller import ResellerContainer
from core.database import get_db
from core.jwt import JWTService, InvalidTokenError, ExpiredTokenError
from src.framework.application.command_bus import CommandBus
from src.framework.application.query_bus import QueryBus
from src.reseller_bc.reseller.domain.entities import Reseller
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

security = HTTPBearer()
jwt_service = JWTService()


def get_current_reseller(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Reseller:
    """Extract and validate JWT with type=reseller, return authenticated reseller."""
    try:
        payload = jwt_service.decode_token(credentials.credentials)
    except ExpiredTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_type = payload.get("type")
    if token_type != "reseller":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    reseller_id = payload.get("sub")
    if not reseller_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = ResellerRepository(db)
    reseller = repo.get_by_id(reseller_id)
    if reseller is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reseller not found")

    if reseller.status == ResellerStatus.DEACTIVATED:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reseller account is deactivated")

    return reseller


def require_active_reseller() -> Callable:
    """Dependency that rejects suspended resellers on write operations."""

    def checker(reseller: Reseller = Depends(get_current_reseller)) -> Reseller:
        if reseller.status == ResellerStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reseller account is suspended",
            )
        return reseller

    return checker


def get_reseller_repo(db: Session = Depends(get_db)) -> ResellerRepository:
    return ResellerRepository(db)


def get_reseller_container(db: Session = Depends(get_db)) -> ResellerContainer:
    return ResellerContainer(db)


def get_reseller_command_bus(
    container: ResellerContainer = Depends(get_reseller_container),
) -> CommandBus:
    return CommandBus(container)


def get_reseller_query_bus(
    container: ResellerContainer = Depends(get_reseller_container),
) -> QueryBus:
    return QueryBus(container)


def get_password_login_service(
    repo: ResellerRepository = Depends(get_reseller_repo),
):
    from core.jwt import JWTService as _JWTService
    from core.password import PasswordService
    from src.reseller_bc.reseller.application.commands.password_login import (
        ResellerPasswordLoginService,
    )

    return ResellerPasswordLoginService(
        repo=repo,
        password_service=PasswordService(),
        jwt_service=_JWTService(),
    )


def get_reseller_google_oauth_service(db: Session = Depends(get_db)):
    from src.reseller_bc.reseller.application.services.reseller_google_oauth import ResellerGoogleOAuthService

    return ResellerGoogleOAuthService(
        repo=ResellerRepository(db),
        jwt_service=JWTService(),
        oauth_settings=settings.oauth,
    )


def get_reseller_microsoft_oauth_service(db: Session = Depends(get_db)):
    from src.reseller_bc.reseller.application.services.reseller_microsoft_oauth import ResellerMicrosoftOAuthService

    return ResellerMicrosoftOAuthService(
        repo=ResellerRepository(db),
        jwt_service=JWTService(),
        oauth_settings=settings.oauth,
    )
