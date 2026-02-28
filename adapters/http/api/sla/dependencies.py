from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.company_bc.sla_escalation_config.infrastructure.repository import (
    SlaEscalationConfigRepository,
)
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


def get_asset_repo(
    db: Session = Depends(get_db),
) -> AssetRepository:
    return AssetRepository(db)


def get_sla_escalation_config_repo(
    db: Session = Depends(get_db),
) -> SlaEscalationConfigRepository:
    return SlaEscalationConfigRepository(db)
