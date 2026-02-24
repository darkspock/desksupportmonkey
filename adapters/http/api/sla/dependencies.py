from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.sla_bc.sla.infrastructure.repository import SlaRepository


def get_sla_repo(
    db: Session = Depends(get_db),
) -> SlaRepository:
    return SlaRepository(db)


def get_request_repo(
    db: Session = Depends(get_db),
) -> RequestRepository:
    return RequestRepository(db)
