from datetime import datetime
from typing import Optional

import ulid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.maintenance_bc.maintenance_record.domain.enums import (
    MaintenancePriority,
    RecurrenceFrequency,
)
from src.maintenance_bc.maintenance_template.domain.entities import (
    ChecklistItem,
    MaintenancePlan,
    MaintenanceTemplate,
)
from src.maintenance_bc.maintenance_template.domain.repository import (
    MaintenancePlanRepositoryInterface,
    MaintenanceTemplateRepositoryInterface,
)
from src.maintenance_bc.maintenance_template.infrastructure.models import (
    MaintenanceChecklistItemModel,
    MaintenancePlanModel,
    MaintenanceTemplateModel,
)


class MaintenanceTemplateRepository(MaintenanceTemplateRepositoryInterface):

    def __init__(self, session: Session):
        self.session = session

    def save(
        self,
        template: MaintenanceTemplate,
    ) -> MaintenanceTemplate:
        model = self.session.execute(
            select(MaintenanceTemplateModel).where(
                MaintenanceTemplateModel.id == template.id,
            )
        ).scalar_one_or_none()

        if model:
            model.name = template.name
            model.description = template.description
            model.default_priority = template.default_priority.value
            model.recurrence_frequency = (
                template.recurrence_frequency.value
                if template.recurrence_frequency
                else None
            )
            model.recurrence_interval = template.recurrence_interval
            model.asset_type_filter = template.asset_type_filter
            model.is_active = template.is_active

            model.checklist_items.clear()
            self.session.flush()
            for idx, item in enumerate(template.checklist_items):
                model.checklist_items.append(
                    MaintenanceChecklistItemModel(
                        id=str(ulid.new()),
                        template_id=template.id,
                        title=item.title,
                        description=item.description,
                        is_required=item.is_required,
                        sort_order=idx,
                    )
                )
        else:
            model = MaintenanceTemplateModel(
                id=template.id,
                company_id=template.company_id,
                name=template.name,
                description=template.description,
                default_priority=template.default_priority.value,
                recurrence_frequency=(
                    template.recurrence_frequency.value
                    if template.recurrence_frequency
                    else None
                ),
                recurrence_interval=template.recurrence_interval,
                asset_type_filter=template.asset_type_filter,
                is_active=template.is_active,
                checklist_items=[
                    MaintenanceChecklistItemModel(
                        id=str(ulid.new()),
                        template_id=template.id,
                        title=item.title,
                        description=item.description,
                        is_required=item.is_required,
                        sort_order=idx,
                    )
                    for idx, item in enumerate(template.checklist_items)
                ],
            )
            self.session.add(model)

        self.session.flush()
        return template

    def find_by_id(
        self,
        template_id: str,
        company_id: str,
    ) -> Optional[MaintenanceTemplate]:
        model = self.session.execute(
            select(MaintenanceTemplateModel).where(
                MaintenanceTemplateModel.id == template_id,
                MaintenanceTemplateModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_template_entity(model)

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: Optional[bool] = None,
    ) -> tuple[list[MaintenanceTemplate], int]:
        stmt = select(MaintenanceTemplateModel).where(
            MaintenanceTemplateModel.company_id == company_id,
        )
        if is_active is not None:
            stmt = stmt.where(
                MaintenanceTemplateModel.is_active == is_active,
            )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery()),
        ).scalar()

        models = self.session.execute(
            stmt.order_by(MaintenanceTemplateModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().unique().all()

        return [self._to_template_entity(m) for m in models], (total or 0)

    def find_by_ids(
        self,
        template_ids: list[str],
        company_id: str,
    ) -> dict[str, MaintenanceTemplate]:
        if not template_ids:
            return {}
        models = self.session.execute(
            select(MaintenanceTemplateModel).where(
                MaintenanceTemplateModel.company_id == company_id,
                MaintenanceTemplateModel.id.in_(template_ids),
            )
        ).scalars().unique().all()
        return {m.id: self._to_template_entity(m) for m in models}

    @staticmethod
    def _to_template_entity(model: MaintenanceTemplateModel) -> MaintenanceTemplate:
        return MaintenanceTemplate(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            description=model.description,
            default_priority=MaintenancePriority(model.default_priority),
            recurrence_frequency=(
                RecurrenceFrequency(model.recurrence_frequency)
                if model.recurrence_frequency
                else None
            ),
            recurrence_interval=model.recurrence_interval,
            asset_type_filter=model.asset_type_filter,
            checklist_items=[
                ChecklistItem(
                    title=item.title,
                    description=item.description,
                    is_required=item.is_required,
                )
                for item in model.checklist_items
            ],
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class MaintenancePlanRepository(MaintenancePlanRepositoryInterface):

    def __init__(self, session: Session):
        self.session = session

    def save(self, plan: MaintenancePlan) -> MaintenancePlan:
        model = self.session.execute(
            select(MaintenancePlanModel).where(
                MaintenancePlanModel.id == plan.id,
            )
        ).scalar_one_or_none()

        if model:
            model.template_id = plan.template_id
            model.asset_id = plan.asset_id
            model.is_active = plan.is_active
            model.next_due_at = plan.next_due_at
            model.last_generated_at = plan.last_generated_at
        else:
            model = MaintenancePlanModel(
                id=plan.id,
                company_id=plan.company_id,
                template_id=plan.template_id,
                asset_id=plan.asset_id,
                is_active=plan.is_active,
                next_due_at=plan.next_due_at,
                last_generated_at=plan.last_generated_at,
            )
            self.session.add(model)

        self.session.flush()
        return plan

    def find_by_id(
        self,
        plan_id: str,
        company_id: str,
    ) -> Optional[MaintenancePlan]:
        model = self.session.execute(
            select(MaintenancePlanModel).where(
                MaintenancePlanModel.id == plan_id,
                MaintenancePlanModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_plan_entity(model)

    def find_all(
        self,
        company_id: str,
        page: int,
        page_size: int,
        is_active: Optional[bool] = None,
        template_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> tuple[list[MaintenancePlan], int]:
        stmt = select(MaintenancePlanModel).where(
            MaintenancePlanModel.company_id == company_id,
        )

        if is_active is not None:
            stmt = stmt.where(
                MaintenancePlanModel.is_active == is_active,
            )
        if template_id:
            stmt = stmt.where(
                MaintenancePlanModel.template_id == template_id,
            )
        if asset_id:
            stmt = stmt.where(
                MaintenancePlanModel.asset_id == asset_id,
            )

        total = self.session.execute(
            select(func.count()).select_from(stmt.subquery()),
        ).scalar()

        models = self.session.execute(
            stmt.order_by(MaintenancePlanModel.next_due_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return [self._to_plan_entity(m) for m in models], (total or 0)

    def find_due_plans(
        self,
        company_id: str,
        due_before: datetime,
    ) -> list[MaintenancePlan]:
        models = self.session.execute(
            select(MaintenancePlanModel).where(
                MaintenancePlanModel.company_id == company_id,
                MaintenancePlanModel.is_active.is_(True),
                MaintenancePlanModel.next_due_at <= due_before,
            )
        ).scalars().all()
        return [self._to_plan_entity(m) for m in models]

    def find_active_by_template_asset(
        self,
        company_id: str,
        template_id: str,
        asset_id: str,
    ) -> Optional[MaintenancePlan]:
        model = self.session.execute(
            select(MaintenancePlanModel).where(
                MaintenancePlanModel.company_id == company_id,
                MaintenancePlanModel.template_id == template_id,
                MaintenancePlanModel.asset_id == asset_id,
                MaintenancePlanModel.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if not model:
            return None
        return self._to_plan_entity(model)

    @staticmethod
    def _to_plan_entity(model: MaintenancePlanModel) -> MaintenancePlan:
        return MaintenancePlan(
            id=model.id,
            company_id=model.company_id,
            template_id=model.template_id,
            asset_id=model.asset_id,
            is_active=model.is_active,
            next_due_at=model.next_due_at,
            last_generated_at=model.last_generated_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
