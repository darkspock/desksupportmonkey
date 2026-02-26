from __future__ import annotations

import ulid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from adapters.http.api.maintenance.mappers import (
    MaintenanceMapper,
)
from src.maintenance_bc.maintenance_record.application.commands.assign_maintenance_record import (
    AssignMaintenanceRecordCommand,
    AssignMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.cancel_maintenance import (
    CancelMaintenanceCommand,
    CancelMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.complete_maintenance import (
    CompleteMaintenanceCommand,
    CompleteMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.create_maintenance_record import (
    CreateMaintenanceRecordCommand,
    CreateMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.skip_maintenance import (
    SkipMaintenanceCommand,
    SkipMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.start_maintenance import (
    StartMaintenanceCommand,
    StartMaintenanceCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.commands.update_maintenance_record import (
    UpdateMaintenanceRecordCommand,
    UpdateMaintenanceRecordCommandHandler,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
    AssetStatusUpdater,
    UserLookup,
)
from src.maintenance_bc.maintenance_record.application.queries.get_maintenance_record import (
    GetMaintenanceRecordQuery,
    GetMaintenanceRecordQueryHandler,
)
from src.maintenance_bc.maintenance_record.application.queries.list_maintenance_records import (
    ListMaintenanceRecordsQuery,
    ListMaintenanceRecordsQueryHandler,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)
from src.notification_bc.notification.application.services.event_bus import (
    EventBus,
)
from src.notification_bc.notification.application.services.maintenance_event_factory import (
    MaintenanceEventFactory,
)


class MaintenanceController:
    def __init__(
        self,
        record_repo: MaintenanceRecordRepository,
        asset_lookup: AssetLookup,
        user_lookup: UserLookup,
        event_bus: EventBus,
        db: Session,
        asset_status_updater: Optional[AssetStatusUpdater] = None,
    ):
        self.record_repo = record_repo
        self.asset_lookup = asset_lookup
        self.user_lookup = user_lookup
        self.event_bus = event_bus
        self.db = db
        self.asset_status_updater = asset_status_updater

    def create(
        self,
        company_id: str,
        actor_id: str,
        asset_id: str,
        title: str,
        priority: str,
        description: Optional[str],
        technician_id: Optional[str],
        template_id: Optional[str],
        plan_id: Optional[str],
        checklist_items: list[str],
        scheduled_at: Optional[datetime],
    ) -> dict:
        record_id = ulid.new().str
        handler = CreateMaintenanceRecordCommandHandler(
            record_repo=self.record_repo,
            asset_lookup=self.asset_lookup,
            user_lookup=self.user_lookup,
        )
        handler.handle(
            CreateMaintenanceRecordCommand(
                record_id=record_id,
                company_id=company_id,
                asset_id=asset_id,
                title=title,
                priority=priority,
                description=description,
                technician_id=technician_id,
                template_id=template_id,
                plan_id=plan_id,
                checklist_items=checklist_items,
                scheduled_at=scheduled_at,
                created_by=actor_id,
            )
        )
        record = self.record_repo.find_by_id(record_id, company_id)
        event = MaintenanceEventFactory.maintenance_scheduled(
            record,
            actor_id=actor_id,
        )
        self.event_bus.publish(event, self.db)
        return {"data": MaintenanceMapper.to_response(record)}

    def list(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str],
        asset_id: Optional[str],
        technician_id: Optional[str],
        priority: Optional[str],
        scheduled_from: Optional[datetime],
        scheduled_to: Optional[datetime],
        search: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        handler = ListMaintenanceRecordsQueryHandler(
            record_repo=self.record_repo,
        )
        records, total = handler.handle(
            ListMaintenanceRecordsQuery(
                company_id=company_id,
                page=page,
                page_size=page_size,
                status=status,
                asset_id=asset_id,
                technician_id=technician_id,
                priority=priority,
                scheduled_from=scheduled_from,
                scheduled_to=scheduled_to,
                search=search,
            )
        )
        return [MaintenanceMapper.to_response(r) for r in records], total

    def get(
        self,
        company_id: str,
        record_id: str,
    ) -> dict:
        handler = GetMaintenanceRecordQueryHandler(
            record_repo=self.record_repo,
        )
        record = handler.handle(
            GetMaintenanceRecordQuery(
                record_id=record_id,
                company_id=company_id,
            )
        )
        return {"data": MaintenanceMapper.to_response(record)}

    def update(
        self,
        company_id: str,
        record_id: str,
        title: Optional[str],
        description: Optional[str],
        priority: Optional[str],
        checklist_items: Optional[list[str]],
        scheduled_at: Optional[datetime],
    ) -> dict:
        handler = UpdateMaintenanceRecordCommandHandler(
            record_repo=self.record_repo,
        )
        handler.handle(
            UpdateMaintenanceRecordCommand(
                record_id=record_id,
                company_id=company_id,
                title=title,
                description=description,
                priority=priority,
                checklist_items=checklist_items,
                scheduled_at=scheduled_at,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        return {"data": MaintenanceMapper.to_response(updated)}

    def assign(
        self,
        company_id: str,
        record_id: str,
        technician_id: str,
    ) -> dict:
        handler = AssignMaintenanceRecordCommandHandler(
            record_repo=self.record_repo,
            user_lookup=self.user_lookup,
        )
        handler.handle(
            AssignMaintenanceRecordCommand(
                record_id=record_id,
                company_id=company_id,
                technician_id=technician_id,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        return {"data": MaintenanceMapper.to_response(updated)}

    def start(
        self,
        company_id: str,
        record_id: str,
    ) -> dict:
        handler = StartMaintenanceCommandHandler(
            record_repo=self.record_repo,
        )
        handler.handle(
            StartMaintenanceCommand(
                record_id=record_id,
                company_id=company_id,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        return {"data": MaintenanceMapper.to_response(updated)}

    def complete(
        self,
        company_id: str,
        actor_id: str,
        record_id: str,
        completion_notes: Optional[str],
        actual_findings: Optional[str],
    ) -> dict:
        handler = CompleteMaintenanceCommandHandler(
            record_repo=self.record_repo,
            asset_status_updater=self.asset_status_updater,
        )
        handler.handle(
            CompleteMaintenanceCommand(
                record_id=record_id,
                company_id=company_id,
                performed_by=actor_id,
                completion_notes=completion_notes,
                actual_findings=actual_findings,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        event = MaintenanceEventFactory.maintenance_completed(
            updated,
            actor_id=actor_id,
        )
        self.event_bus.publish(event, self.db)
        return {"data": MaintenanceMapper.to_response(updated)}

    def cancel(
        self,
        company_id: str,
        actor_id: str,
        record_id: str,
        reason: str,
    ) -> dict:
        handler = CancelMaintenanceCommandHandler(
            record_repo=self.record_repo,
        )
        handler.handle(
            CancelMaintenanceCommand(
                record_id=record_id,
                company_id=company_id,
                reason=reason,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        event = MaintenanceEventFactory.maintenance_cancelled(
            updated,
            actor_id=actor_id,
        )
        self.event_bus.publish(event, self.db)
        return {"data": MaintenanceMapper.to_response(updated)}

    def skip(
        self,
        company_id: str,
        record_id: str,
        reason: str,
    ) -> dict:
        handler = SkipMaintenanceCommandHandler(
            record_repo=self.record_repo,
        )
        handler.handle(
            SkipMaintenanceCommand(
                record_id=record_id,
                company_id=company_id,
                reason=reason,
            )
        )
        updated = self.record_repo.find_by_id(record_id, company_id)
        return {"data": MaintenanceMapper.to_response(updated)}
