from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorRiskAssessmentRepository,
)


def get_assessment_repo(
    db: Session = Depends(get_db),
) -> VendorRiskAssessmentRepository:
    return VendorRiskAssessmentRepository(db)
