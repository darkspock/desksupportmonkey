import json
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.infrastructure.models import AssetModel
from src.auth_bc.user.infrastructure.models import UserModel

from src.maintenance_bc.maintenance_record.domain.entities import MaintenanceRecord
from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    MaintenanceStatus,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)
from src.maintenance_bc.maintenance_record.infrastructure.models import (
    MaintenanceRecordModel,
)


class MaintenanceRecordRepository(MaintenanceRecordRepositoryInterface):

    def __init__(self, session: Session):
        self.session = session

    def save(self, record: MaintenanceRecord) -> MaintenanceRecord:
        model = self.session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.id == record.id,
            )
        ).scalar_one_or_none()

        serialized_items = json.dumps(record.checklist_items)

        if model:
            model.status = record.status.value
            model.priority = record.priority.value
            model.title = record.title
            model.description = record.description
            model.technician_id = record.technician_id
            model.template_id = record.template_id
            model.plan_id = record.plan_id
            model.checklist_items = serialized_items
            model.scheduled_at = record.scheduled_at
            model.started_at = record.started_at
            model.completed_at = record.completed_at
            model.completion_notes = record.completion_notes
            model.actual_findings = record.actual_findings
            model.cancellation_reason = record.cancellation_reason
            model.skip_reason = record.skip_reason
            model.source_type = record.source_type
            model.reminder_48h_sent = record.reminder_48h_sent
            model.overdue_alert_sent = record.overdue_alert_sent
        else:
            model = MaintenanceRecordModel(
                id=record.id,
                company_id=record.company_id,
                asset_id=record.asset_id,
                status=record.status.value,
                priority=record.priority.value,
                title=record.title,
                description=record.description,
                technician_id=record.technician_id,
                template_id=record.template_id,
                plan_id=record.plan_id,
                checklist_items=serialized_items,
                scheduled_at=record.scheduled_at,
                started_at=record.started_at,
                completed_at=record.completed_at,
                completion_notes=record.completion_notes,
                actual_findings=record.actual_findings,
                cancellation_reason=record.cancellation_reason,
                skip_reason=record.skip_reason,
                source_type=record.source_type,
                reminder_48h_sent=record.reminder_48h_sent,
                overdue_alert_sent=record.overdue_alert_sent,
            )
            self.session.add(model)

        self.session.flush()
        return record

    def find_by_id(
        self,
        record_id: str,
        company_id: str,
    ) -> Optional[MaintenanceRecord]:
        model = self.session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.id == record_id,
                MaintenanceRecordModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        asset_id: Optional[str] = None,
        technician_id: Optional[str] = None,
        priority: Optional[str] = None,
        scheduled_from: Optional[datetime] = None,
        scheduled_to: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> tuple[list[MaintenanceRecord], int]:
        employee = UserModel.__table__.alias("employee")
        stmt = (
            select(
                MaintenanceRecordModel,
                employee.c.name.label("employee_name"),
                employee.c.email.label("employee_email"),
            )
            .outerjoin(
                AssetModel,
                AssetModel.id == MaintenanceRecordModel.asset_id,
            )
            .outerjoin(
                employee,
                employee.c.id == AssetModel.assigned_to,
            )
            .where(MaintenanceRecordModel.company_id == company_id)
        )

        if status:
            stmt = stmt.where(MaintenanceRecordModel.status == status)
        if asset_id:
            stmt = stmt.where(MaintenanceRecordModel.asset_id == asset_id)
        if technician_id:
            stmt = stmt.where(
                MaintenanceRecordModel.technician_id == technician_id,
            )
        if priority:
            stmt = stmt.where(
                MaintenanceRecordModel.priority == priority,
            )
        if scheduled_from:
            stmt = stmt.where(
                MaintenanceRecordModel.scheduled_at >= scheduled_from,
            )
        if scheduled_to:
            stmt = stmt.where(
                MaintenanceRecordModel.scheduled_at <= scheduled_to,
            )
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    MaintenanceRecordModel.id.ilike(pattern),
                    MaintenanceRecordModel.title.ilike(pattern),
                    MaintenanceRecordModel.description.ilike(pattern),
                    employee.c.name.ilike(pattern),
                    employee.c.email.ilike(pattern),
                )
            )

        count_sub = stmt.with_only_columns(
            func.count(MaintenanceRecordModel.id),
        ).order_by(None)
        total = self.session.execute(count_sub).scalar()

        rows = self.session.execute(
            stmt.order_by(MaintenanceRecordModel.scheduled_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        results: list[MaintenanceRecord] = []
        for row in rows:
            model = row[0]
            entity = self._to_entity(model)
            entity.employee_name = row.employee_name
            entity.employee_email = row.employee_email
            results.append(entity)

        return results, (total or 0)

    def find_due_within_hours(
        self,
        company_id: str,
        hours: int,
    ) -> list[MaintenanceRecord]:
        now = datetime.now(UTC)
        due_limit = now + timedelta(hours=hours)
        models = self.session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.company_id == company_id,
                MaintenanceRecordModel.status == MaintenanceStatus.SCHEDULED.value,
                MaintenanceRecordModel.scheduled_at.is_not(None),
                MaintenanceRecordModel.scheduled_at <= due_limit,
                MaintenanceRecordModel.scheduled_at >= now,
                MaintenanceRecordModel.reminder_48h_sent.is_(False),
            )
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_overdue(
        self,
        company_id: str,
    ) -> list[MaintenanceRecord]:
        now = datetime.now(UTC)
        models = self.session.execute(
            select(MaintenanceRecordModel).where(
                MaintenanceRecordModel.company_id == company_id,
                MaintenanceRecordModel.status == MaintenanceStatus.SCHEDULED.value,
                MaintenanceRecordModel.scheduled_at.is_not(None),
                MaintenanceRecordModel.scheduled_at < now,
                MaintenanceRecordModel.overdue_alert_sent.is_(False),
            )
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_dashboard(self, company_id: str) -> dict[str, int]:
        rows = self.session.execute(
            select(
                MaintenanceRecordModel.status,
                func.count(MaintenanceRecordModel.id),
            )
            .where(MaintenanceRecordModel.company_id == company_id)
            .group_by(MaintenanceRecordModel.status)
        ).all()

        counts = {
            "scheduled": 0,
            "overdue": 0,
            "in_progress": 0,
            "completed_30d": 0,
        }

        for status, amount in rows:
            if status == MaintenanceStatus.SCHEDULED.value:
                counts["scheduled"] = int(amount)
            elif status == MaintenanceStatus.IN_PROGRESS.value:
                counts["in_progress"] = int(amount)

        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        completed_30d = self.session.execute(
            select(func.count(MaintenanceRecordModel.id)).where(
                MaintenanceRecordModel.company_id == company_id,
                MaintenanceRecordModel.status == MaintenanceStatus.COMPLETED.value,
                MaintenanceRecordModel.completed_at.is_not(None),
                MaintenanceRecordModel.completed_at >= thirty_days_ago,
            )
        ).scalar()
        overdue = self.session.execute(
            select(func.count(MaintenanceRecordModel.id)).where(
                MaintenanceRecordModel.company_id == company_id,
                MaintenanceRecordModel.status == MaintenanceStatus.SCHEDULED.value,
                MaintenanceRecordModel.scheduled_at.is_not(None),
                MaintenanceRecordModel.scheduled_at < datetime.now(UTC),
            )
        ).scalar()

        counts["completed_30d"] = int(completed_30d or 0)
        counts["overdue"] = int(overdue or 0)

        return counts

    def find_my_queue(
        self,
        company_id: str,
        technician_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[MaintenanceRecord], int]:
        stmt = select(MaintenanceRecordModel).where(
            MaintenanceRecordModel.company_id == company_id,
            MaintenanceRecordModel.technician_id == technician_id,
            MaintenanceRecordModel.status.in_(
                [
                    MaintenanceStatus.SCHEDULED.value,
                    MaintenanceStatus.IN_PROGRESS.value,
                ]
            ),
        )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery()),
        ).scalar()

        models = self.session.execute(
            stmt.order_by(MaintenanceRecordModel.scheduled_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return [self._to_entity(m) for m in models], (total or 0)

    @staticmethod
    def _to_entity(model: MaintenanceRecordModel) -> MaintenanceRecord:
        return MaintenanceRecord(
            id=model.id,
            company_id=model.company_id,
            asset_id=model.asset_id,
            status=MaintenanceStatus(model.status),
            priority=MaintenancePriority(model.priority),
            title=model.title,
            description=model.description,
            technician_id=model.technician_id,
            template_id=model.template_id,
            plan_id=model.plan_id,
            checklist_items=(json.loads(model.checklist_items) if model.checklist_items else []),
            scheduled_at=model.scheduled_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            completion_notes=model.completion_notes,
            actual_findings=model.actual_findings,
            cancellation_reason=model.cancellation_reason,
            skip_reason=model.skip_reason,
            source_type=model.source_type,
            reminder_48h_sent=model.reminder_48h_sent,
            overdue_alert_sent=model.overdue_alert_sent,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
