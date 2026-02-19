from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.appointment_bc.appointment.infrastructure.repository import (
    AvailabilityOverrideRepository,
    TechnicianAvailabilityRepository,
)


def get_availability_repo(
    db: Session = Depends(get_db),
) -> TechnicianAvailabilityRepository:
    return TechnicianAvailabilityRepository(db)


def get_override_repo(
    db: Session = Depends(get_db),
) -> AvailabilityOverrideRepository:
    return AvailabilityOverrideRepository(db)
