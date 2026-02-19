from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus, ReportType
from src.report_bc.report.domain.repository import ReportRepositoryInterface
from src.report_bc.report.infrastructure.models import ReportModel


class ReportRepository(ReportRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, report: Report) -> Report:
        model = ReportModel(
            id=report.id,
            company_id=report.company_id,
            requested_by=report.requested_by,
            type=report.type.value,
            status=report.status.value,
            parameters=report.parameters,
            storage_key=report.storage_key,
            error_message=report.error_message,
            completed_at=report.completed_at,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, report_id: str, company_id: str) -> Optional[Report]:
        model = self.session.execute(
            select(ReportModel).where(
                ReportModel.id == report_id,
                ReportModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_id_any_company(self, report_id: str) -> Optional[Report]:
        model = self.session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_all(
        self, company_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Report], int]:
        stmt = select(ReportModel).where(ReportModel.company_id == company_id)

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        models = self.session.execute(
            stmt.order_by(ReportModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return [self._to_entity(m) for m in models], total or 0

    def update_status(
        self,
        report_id: str,
        status: ReportStatus,
        storage_key: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool:
        values: dict = {"status": status.value}
        if storage_key is not None:
            values["storage_key"] = storage_key
        if error_message is not None:
            values["error_message"] = error_message
        if completed_at is not None:
            values["completed_at"] = completed_at
        elif status in (ReportStatus.COMPLETED, ReportStatus.FAILED):
            values["completed_at"] = datetime.now(timezone.utc)

        result = self.session.execute(
            update(ReportModel).where(ReportModel.id == report_id).values(**values)
        )
        return result.rowcount > 0

    @staticmethod
    def _to_entity(model: ReportModel) -> Report:
        return Report(
            id=model.id,
            company_id=model.company_id,
            requested_by=model.requested_by,
            type=ReportType(model.type),
            status=ReportStatus(model.status),
            parameters=model.parameters,
            storage_key=model.storage_key,
            error_message=model.error_message,
            created_at=model.created_at,
            completed_at=model.completed_at,
            updated_at=model.updated_at,
        )
