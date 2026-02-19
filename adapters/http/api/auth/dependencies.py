from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from core.database import get_db
from core.jwt import JWTService, InvalidTokenError, ExpiredTokenError
from core.tenant import set_tenant
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository

security = HTTPBearer()
jwt_service = JWTService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT, return authenticated user."""
    try:
        payload = jwt_service.decode_token(credentials.credentials)
    except ExpiredTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = UserRepository(db)
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    # Check company status (skip for super admins with no company)
    if user.company_id:
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        from src.company_bc.company.domain.enums import CompanyStatus

        company_repo = CompanyRepository(db)
        company = company_repo.find_by_id(user.company_id)
        if company and company.status != CompanyStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company access is currently restricted",
            )

    # Set tenant context
    set_tenant(company_id=user.company_id, user_id=user.id, role=user.role.value)

    return user


def require_role(minimum_role: UserRole) -> Callable:
    """Factory that returns a dependency checking minimum role level."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role.has_access(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_magic_link_repo(db: Session = Depends(get_db)) -> MagicLinkRepository:
    return MagicLinkRepository(db)


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)
