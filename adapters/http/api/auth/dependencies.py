from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from core.config import settings
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

    token_type = payload.get("type", "user")
    if token_type != "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    repo = UserRepository(db)
    user = repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    # Session invalidation: JWT company_id must match user row's company_id
    jwt_company_id = payload.get("company_id")
    if jwt_company_id is not None and user.company_id != jwt_company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired — please log in again",
        )

    # Check company status (skip for super admins with no company)
    if user.company_id:
        from datetime import timedelta, datetime, timezone
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        from src.company_bc.company.infrastructure.models import CompanyModel
        from src.company_bc.company.domain.enums import CompanyStatus
        from src.company_bc.company.domain.billing_enums import BillingStatus
        from core.config import settings as _settings

        company_repo = CompanyRepository(db)
        company = company_repo.find_by_id(user.company_id)
        if company and company.status != CompanyStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company access is currently restricted",
            )

        # Lazy grace period expiry: suspend if 15 days have elapsed
        if (
            company
            and not _settings.stripe.OPEN_SOURCE_MODE
            and not company.is_in_trial()
            and company.billing_status == BillingStatus.GRACE_PERIOD
            and company.grace_period_started_at
        ):
            started = company.grace_period_started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if started + timedelta(days=15) < datetime.now(timezone.utc):
                # ORM-level update (WHERE guard) so session identity map stays consistent
                from sqlalchemy import select as sqlalchemy_select
                model = db.execute(
                    sqlalchemy_select(CompanyModel)
                    .where(CompanyModel.id == company.id)
                    .where(CompanyModel.billing_status == "grace_period")
                ).scalar_one_or_none()
                if model:
                    model.billing_status = "suspended"
                    db.flush()
                    company.billing_status = BillingStatus.SUSPENDED

    # Set tenant context
    set_tenant(company_id=user.company_id, user_id=user.id, role=user.role.value)

    return user


def require_plan_feature(feature: str) -> Callable:
    """Factory returning a dependency that raises 402 if feature not available."""

    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        from src.company_bc.company.domain.plan_gate import PlanGate
        from core.config import settings as _settings

        if not current_user.company_id:
            return current_user
        company = CompanyRepository(db).find_by_id(current_user.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company not found",
            )
        if not PlanGate.is_feature_available(
            plan=company.plan,
            billing_status=company.billing_status,
            complimentary=company.complimentary,
            open_source_mode=_settings.stripe.OPEN_SOURCE_MODE,
            feature=feature,
            in_trial=company.is_in_trial(),
        ):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Feature '{feature}' requires an upgrade",
            )
        return current_user

    return checker


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
