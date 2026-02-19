from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

import ulid

from src.framework.application.command_bus import (
    Command,
    CommandHandler,
)
from src.maintenance_bc.maintenance_record.domain.entities import (
    MaintenanceRecord,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
)
from src.maintenance_bc.maintenance_template.application.services.recurrence import (
    compute_next_due,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenancePlan,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenancePlanRepositoryInterface,
    MaintenanceTemplateRepositoryInterface,
)
from src.maintenance_bc.maintenance_record.domain.repository import (
    MaintenanceRecordRepositoryInterface,
)


class MaintenanceTemplateNotFoundError(Exception):
    pass


@dataclass
class ApplyTemplateToAssetsCommand(Command):
    template_id: str
    company_id: str
    asset_ids: Optional[list[str]] = None
    first_due_at: Optional[datetime] = None


class ApplyTemplateToAssetsCommandHandler(
    CommandHandler[ApplyTemplateToAssetsCommand],
):
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepositoryInterface,
        plan_repo: MaintenancePlanRepositoryInterface,
        record_repo: MaintenanceRecordRepositoryInterface,
        asset_lookup: AssetLookup,
    ):
        self.template_repo = template_repo
        self.plan_repo = plan_repo
        self.record_repo = record_repo
        self.asset_lookup = asset_lookup

    def handle(
        self,
        command: ApplyTemplateToAssetsCommand,
    ) -> None:
        template = self.template_repo.find_by_id(
            command.template_id,
            command.company_id,
        )
        if not template:
            raise MaintenanceTemplateNotFoundError("Maintenance template not found")
        if not template.is_active:
            raise ValueError("Cannot apply inactive template")
        if template.recurrence_frequency is None:
            raise ValueError("Template recurrence_frequency is required for plan generation")

        candidate_assets = self.asset_lookup.list_by_company(
            command.company_id,
        )
        if template.asset_type_filter:
            candidate_assets = [
                a for a in candidate_assets if a.type == template.asset_type_filter
            ]

        if command.asset_ids:
            asset_ids_set = set(command.asset_ids)
            candidate_assets = [
                a for a in candidate_assets if a.id in asset_ids_set
            ]

        first_due_at = command.first_due_at or datetime.now(UTC)
        checklist_snapshot = [item.title for item in template.checklist_items]

        for asset in candidate_assets:
            existing = self.plan_repo.find_active_by_template_asset(
                company_id=command.company_id,
                template_id=template.id,
                asset_id=asset.id,
            )
            if existing:
                continue

            next_due = compute_next_due(
                base=first_due_at,
                frequency=template.recurrence_frequency,
                interval=template.recurrence_interval,
            )

            plan = MaintenancePlan.create(
                id=str(ulid.new()),
                company_id=command.company_id,
                template_id=template.id,
                asset_id=asset.id,
                next_due_at=next_due,
            )
            plan.update_next_due(
                next_due_at=next_due,
                last_generated_at=first_due_at,
            )
            self.plan_repo.save(plan)

            record = MaintenanceRecord.create(
                id=str(ulid.new()),
                company_id=command.company_id,
                asset_id=asset.id,
                title=template.name,
                priority=template.default_priority,
                description=template.description,
                template_id=template.id,
                plan_id=plan.id,
                checklist_items=checklist_snapshot,
                scheduled_at=first_due_at,
            )
            self.record_repo.save(record)
