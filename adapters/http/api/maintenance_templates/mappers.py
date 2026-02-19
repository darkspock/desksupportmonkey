from adapters.http.api.maintenance_templates.schemas import (
    ChecklistItemResponse,
    MaintenancePlanResponse,
    MaintenanceTemplateResponse,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    MaintenancePlan,
    MaintenanceTemplate,
)


class MaintenanceTemplateMapper:
    @staticmethod
    def template_to_response(
        template: MaintenanceTemplate,
    ) -> dict:
        return MaintenanceTemplateResponse(
            id=template.id,
            company_id=template.company_id,
            name=template.name,
            default_priority=template.default_priority.value,
            description=template.description,
            recurrence_frequency=(
                template.recurrence_frequency.value
                if template.recurrence_frequency
                else None
            ),
            recurrence_interval=template.recurrence_interval,
            asset_type_filter=template.asset_type_filter,
            checklist_items=[
                ChecklistItemResponse(
                    title=i.title,
                    description=i.description,
                    is_required=i.is_required,
                )
                for i in template.checklist_items
            ],
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        ).model_dump(mode="json")

    @staticmethod
    def plan_to_response(plan: MaintenancePlan) -> dict:
        return MaintenancePlanResponse(
            id=plan.id,
            company_id=plan.company_id,
            template_id=plan.template_id,
            asset_id=plan.asset_id,
            is_active=plan.is_active,
            next_due_at=plan.next_due_at,
            last_generated_at=plan.last_generated_at,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        ).model_dump(mode="json")
