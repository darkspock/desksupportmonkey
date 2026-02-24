from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.audit_bc.audit.infrastructure.repository import AuditRepository
from src.auth_bc.user.infrastructure.repository import UserRepository


def get_audit_repo(
    db: Session = Depends(get_db),
) -> AuditRepository:
    return AuditRepository(db)


def get_user_repo(
    db: Session = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)
