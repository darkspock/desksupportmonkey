import ulid

from adapters.http.api.maintenance_templates.mappers import (
    MaintenanceTemplateMapper,
)
from src.maintenance_bc.maintenance_record.application.ports import (
    AssetLookup,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)
from src.maintenance_bc.maintenance_template.application.commands.apply_template_to_assets import (
    ApplyTemplateToAssetsCommand,
    ApplyTemplateToAssetsCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.create_maintenance_template import (
    CreateMaintenanceTemplateCommand,
    CreateMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.deactivate_plan import (
    DeactivatePlanCommand,
    DeactivatePlanCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.delete_maintenance_template import (
    DeleteMaintenanceTemplateCommand,
    DeleteMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.commands.update_maintenance_template import (
    UpdateMaintenanceTemplateCommand,
    UpdateMaintenanceTemplateCommandHandler,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_plan import (
    GetMaintenancePlanQuery,
    GetMaintenancePlanQueryHandler,
)
from src.maintenance_bc.maintenance_template.application.queries.get_maintenance_template import (
    GetMaintenanceTemplateQuery,
    GetMaintenanceTemplateQueryHandler,
)
from src.maintenance_bc.maintenance_template.application.queries.list_maintenance_plans import (
    ListMaintenancePlansQuery,
    ListMaintenancePlansQueryHandler,
)
from src.maintenance_bc.maintenance_template.application.queries.list_maintenance_templates import (
    ListMaintenanceTemplatesQuery,
    ListMaintenanceTemplatesQueryHandler,
)
from src.maintenance_bc.maintenance_template.infrastructure.repository import (
    MaintenancePlanRepository,
    MaintenanceTemplateRepository,
)


class MaintenanceTemplatesController:
    def __init__(
        self,
        template_repo: MaintenanceTemplateRepository,
        plan_repo: MaintenancePlanRepository,
        record_repo: MaintenanceRecordRepository,
        asset_lookup: AssetLookup,
    ):
        self.template_repo = template_repo
        self.plan_repo = plan_repo
        self.record_repo = record_repo
        self.asset_lookup = asset_lookup

    def create_template(
        self,
        company_id: str,
        name: str,
        default_priority: str,
        description: str | None,
        recurrence_frequency: str | None,
        recurrence_interval: int,
        asset_type_filter: str | None,
        checklist_items: list[dict],
    ) -> dict:
        template_id = ulid.new().str
        handler = CreateMaintenanceTemplateCommandHandler(
            template_repo=self.template_repo,
        )
        handler.handle(
            CreateMaintenanceTemplateCommand(
                template_id=template_id,
                company_id=company_id,
                name=name,
                default_priority=default_priority,
                description=description,
                recurrence_frequency=recurrence_frequency,
                recurrence_interval=recurrence_interval,
                asset_type_filter=asset_type_filter,
                checklist_items=checklist_items,
            )
        )
        template = self.template_repo.find_by_id(template_id, company_id)
        return {"data": MaintenanceTemplateMapper.template_to_response(template)}

    def list_templates(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: bool | None,
    ) -> tuple[list[dict], int]:
        handler = ListMaintenanceTemplatesQueryHandler(
            template_repo=self.template_repo,
        )
        templates, total = handler.handle(
            ListMaintenanceTemplatesQuery(
                company_id=company_id,
                page=page,
                page_size=page_size,
                is_active=is_active,
            )
        )
        return [
            MaintenanceTemplateMapper.template_to_response(t)
            for t in templates
        ], total

    def get_template(
        self,
        company_id: str,
        template_id: str,
    ) -> dict:
        handler = GetMaintenanceTemplateQueryHandler(
            template_repo=self.template_repo,
        )
        template = handler.handle(
            GetMaintenanceTemplateQuery(
                template_id=template_id,
                company_id=company_id,
            )
        )
        return {"data": MaintenanceTemplateMapper.template_to_response(template)}

    def update_template(
        self,
        company_id: str,
        template_id: str,
        name: str | None,
        default_priority: str | None,
        description: str | None,
        recurrence_frequency: str | None,
        recurrence_interval: int | None,
        asset_type_filter: str | None,
        checklist_items: list[dict] | None,
    ) -> dict:
        handler = UpdateMaintenanceTemplateCommandHandler(
            template_repo=self.template_repo,
        )
        handler.handle(
            UpdateMaintenanceTemplateCommand(
                template_id=template_id,
                company_id=company_id,
                name=name,
                default_priority=default_priority,
                description=description,
                recurrence_frequency=recurrence_frequency,
                recurrence_interval=recurrence_interval,
                asset_type_filter=asset_type_filter,
                checklist_items=checklist_items,
            )
        )
        template = self.template_repo.find_by_id(template_id, company_id)
        return {"data": MaintenanceTemplateMapper.template_to_response(template)}

    def delete_template(
        self,
        company_id: str,
        template_id: str,
    ) -> dict:
        handler = DeleteMaintenanceTemplateCommandHandler(
            template_repo=self.template_repo,
        )
        handler.handle(
            DeleteMaintenanceTemplateCommand(
                template_id=template_id,
                company_id=company_id,
            )
        )
        template = self.template_repo.find_by_id(template_id, company_id)
        return {"data": MaintenanceTemplateMapper.template_to_response(template)}

    def apply_template(
        self,
        company_id: str,
        template_id: str,
        asset_ids: list[str] | None,
        first_due_at,
    ) -> dict:
        handler = ApplyTemplateToAssetsCommandHandler(
            template_repo=self.template_repo,
            plan_repo=self.plan_repo,
            record_repo=self.record_repo,
            asset_lookup=self.asset_lookup,
        )
        handler.handle(
            ApplyTemplateToAssetsCommand(
                template_id=template_id,
                company_id=company_id,
                asset_ids=asset_ids,
                first_due_at=first_due_at,
            )
        )
        return {"data": {"success": True}}

    def list_plans(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: bool | None,
        template_id: str | None,
        asset_id: str | None,
    ) -> tuple[list[dict], int]:
        handler = ListMaintenancePlansQueryHandler(
            plan_repo=self.plan_repo,
        )
        plans, total = handler.handle(
            ListMaintenancePlansQuery(
                company_id=company_id,
                page=page,
                page_size=page_size,
                is_active=is_active,
                template_id=template_id,
                asset_id=asset_id,
            )
        )
        return [
            MaintenanceTemplateMapper.plan_to_response(p)
            for p in plans
        ], total

    def get_plan(
        self,
        company_id: str,
        plan_id: str,
    ) -> dict:
        handler = GetMaintenancePlanQueryHandler(
            plan_repo=self.plan_repo,
        )
        plan = handler.handle(
            GetMaintenancePlanQuery(
                plan_id=plan_id,
                company_id=company_id,
            )
        )
        return {"data": MaintenanceTemplateMapper.plan_to_response(plan)}

    def deactivate_plan(
        self,
        company_id: str,
        plan_id: str,
    ) -> dict:
        handler = DeactivatePlanCommandHandler(
            plan_repo=self.plan_repo,
        )
        handler.handle(
            DeactivatePlanCommand(
                plan_id=plan_id,
                company_id=company_id,
            )
        )
        plan = self.plan_repo.find_by_id(plan_id, company_id)
        return {"data": MaintenanceTemplateMapper.plan_to_response(plan)}
