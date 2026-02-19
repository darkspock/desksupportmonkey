from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.appointment_bc.appointment.infrastructure.repository import (
    AppointmentRepository,
)


def get_appointment_repo(
    db: Session = Depends(get_db),
) -> AppointmentRepository:
    return AppointmentRepository(db)
