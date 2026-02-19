from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.report_bc.report.infrastructure.repository import ReportRepository


def get_report_repo(db: Session = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)
