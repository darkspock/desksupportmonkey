from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from adapters.http.api.maintenance.schemas import (
    MaintenanceRecordResponse,
)


class MaintenanceMapper:
    @staticmethod
    def to_response(record: MaintenanceRecord) -> dict:
        return MaintenanceRecordResponse(
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
            checklist_items=record.checklist_items,
            scheduled_at=record.scheduled_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            completion_notes=record.completion_notes,
            actual_findings=record.actual_findings,
            cancellation_reason=record.cancellation_reason,
            skip_reason=record.skip_reason,
            reminder_48h_sent=record.reminder_48h_sent,
            overdue_alert_sent=record.overdue_alert_sent,
            created_at=record.created_at,
            updated_at=record.updated_at,
        ).model_dump(mode="json")
