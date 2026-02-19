from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from src.auth_bc.user.domain.enums import UserRole

_tenant_company_id: ContextVar[Optional[str]] = ContextVar("tenant_company_id", default=None)
_tenant_user_id: ContextVar[Optional[str]] = ContextVar("tenant_user_id", default=None)
_tenant_role: ContextVar[Optional[str]] = ContextVar("tenant_role", default=None)


@dataclass
class TenantContext:
    company_id: Optional[str]
    user_id: str
    role: str


def set_tenant(company_id: Optional[str], user_id: str, role: str) -> None:
    _tenant_company_id.set(company_id)
    _tenant_user_id.set(user_id)
    _tenant_role.set(role)


def get_tenant() -> Optional[TenantContext]:
    user_id = _tenant_user_id.get()
    if user_id is None:
        return None
    return TenantContext(
        company_id=_tenant_company_id.get(),
        user_id=user_id,
        role=_tenant_role.get() or "",
    )


def get_tenant_company_id() -> Optional[str]:
    return _tenant_company_id.get()


def clear_tenant() -> None:
    _tenant_company_id.set(None)
    _tenant_user_id.set(None)
    _tenant_role.set(None)


def is_super_admin() -> bool:
    return _tenant_role.get() == UserRole.SUPER_ADMIN.value
