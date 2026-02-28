from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.company_bc.sla_escalation_config.infrastructure.repository import (
    SlaEscalationConfigRepository,
)


def get_sla_escalation_config_repo(
    db: Session = Depends(get_db),
) -> SlaEscalationConfigRepository:
    return SlaEscalationConfigRepository(db)
