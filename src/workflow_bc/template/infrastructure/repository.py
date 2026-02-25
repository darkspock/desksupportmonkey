from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.workflow_bc.template.domain.entities import (
    ChecklistItemDefinition,
    WorkflowSubtype,
    WorkflowTemplate,
)
from src.workflow_bc.template.domain.repository import WorkflowTemplateRepositoryInterface
from src.workflow_bc.template.infrastructure.models import (
    ChecklistItemDefinitionModel,
    WorkflowSubtypeModel,
    WorkflowTemplateModel,
)


class WorkflowTemplateRepository(WorkflowTemplateRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def _model_to_entity(self, m: WorkflowTemplateModel) -> WorkflowTemplate:
        subtypes = (
            self.session.execute(
                select(WorkflowSubtypeModel)
                .where(WorkflowSubtypeModel.template_id == m.id)
                .order_by(WorkflowSubtypeModel.sort_order)
            )
            .scalars()
            .all()
        )
        items = (
            self.session.execute(
                select(ChecklistItemDefinitionModel)
                .where(ChecklistItemDefinitionModel.template_id == m.id)
                .order_by(ChecklistItemDefinitionModel.sort_order)
            )
            .scalars()
            .all()
        )
        return WorkflowTemplate(
            id=m.id,
            company_id=m.company_id,
            name=m.name,
            description=m.description,
            icon=m.icon,
            is_active=m.is_active,
            require_all_complete=m.require_all_complete,
            sort_order=m.sort_order,
            subtypes=[
                WorkflowSubtype(
                    id=s.id,
                    template_id=s.template_id,
                    name=s.name,
                    description=s.description,
                    sort_order=s.sort_order,
                    is_active=s.is_active,
                )
                for s in subtypes
            ],
            checklist_items=[
                ChecklistItemDefinition(
                    id=ci.id,
                    template_id=ci.template_id,
                    title=ci.title,
                    description=ci.description,
                    assignee_role=ci.assignee_role,
                    sort_order=ci.sort_order,
                    is_required=ci.is_required,
                )
                for ci in items
            ],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def save(self, template: WorkflowTemplate) -> None:
        existing = self.session.execute(
            select(WorkflowTemplateModel).where(
                WorkflowTemplateModel.id == template.id
            )
        ).scalar_one_or_none()

        if existing:
            existing.name = template.name
            existing.description = template.description
            existing.icon = template.icon
            existing.is_active = template.is_active
            existing.require_all_complete = template.require_all_complete
            existing.sort_order = template.sort_order
            existing.updated_at = template.updated_at
        else:
            model = WorkflowTemplateModel(
                id=template.id,
                company_id=template.company_id,
                name=template.name,
                description=template.description,
                icon=template.icon,
                is_active=template.is_active,
                require_all_complete=template.require_all_complete,
                sort_order=template.sort_order,
                created_at=template.created_at,
                updated_at=template.updated_at,
            )
            self.session.add(model)

        self.session.flush()

        # Sync subtypes: delete removed, upsert current
        self._sync_subtypes(template.id, template.subtypes)
        # Sync checklist items: delete removed, upsert current
        self._sync_checklist_items(template.id, template.checklist_items)

    def _sync_subtypes(self, template_id: str, subtypes: list[WorkflowSubtype]) -> None:
        existing_models = (
            self.session.execute(
                select(WorkflowSubtypeModel).where(
                    WorkflowSubtypeModel.template_id == template_id
                )
            )
            .scalars()
            .all()
        )
        existing_by_id = {m.id: m for m in existing_models}
        new_ids = {s.id for s in subtypes}

        # Disable removed (not in the incoming list)
        for m in existing_models:
            if m.id not in new_ids:
                m.is_active = False

        # Upsert current
        for s in subtypes:
            if s.id in existing_by_id:
                m = existing_by_id[s.id]
                m.name = s.name
                m.description = s.description
                m.sort_order = s.sort_order
                m.is_active = s.is_active
            else:
                self.session.add(
                    WorkflowSubtypeModel(
                        id=s.id,
                        template_id=template_id,
                        name=s.name,
                        description=s.description,
                        sort_order=s.sort_order,
                        is_active=s.is_active,
                    )
                )
        self.session.flush()

    def _sync_checklist_items(
        self, template_id: str, items: list[ChecklistItemDefinition]
    ) -> None:
        existing_models = (
            self.session.execute(
                select(ChecklistItemDefinitionModel).where(
                    ChecklistItemDefinitionModel.template_id == template_id
                )
            )
            .scalars()
            .all()
        )
        existing_by_id = {m.id: m for m in existing_models}
        new_ids = {ci.id for ci in items}

        for m in existing_models:
            if m.id not in new_ids:
                self.session.delete(m)

        for ci in items:
            if ci.id in existing_by_id:
                m = existing_by_id[ci.id]
                m.title = ci.title
                m.description = ci.description
                m.assignee_role = ci.assignee_role
                m.sort_order = ci.sort_order
                m.is_required = ci.is_required
            else:
                self.session.add(
                    ChecklistItemDefinitionModel(
                        id=ci.id,
                        template_id=template_id,
                        title=ci.title,
                        description=ci.description,
                        assignee_role=ci.assignee_role,
                        sort_order=ci.sort_order,
                        is_required=ci.is_required,
                    )
                )
        self.session.flush()

    def find_by_id(self, id: str, company_id: str) -> Optional[WorkflowTemplate]:
        m = self.session.execute(
            select(WorkflowTemplateModel).where(
                WorkflowTemplateModel.id == id,
                WorkflowTemplateModel.company_id == company_id,
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def find_by_company(
        self, company_id: str, active_only: bool = False
    ) -> list[WorkflowTemplate]:
        stmt = select(WorkflowTemplateModel).where(
            WorkflowTemplateModel.company_id == company_id
        )
        if active_only:
            stmt = stmt.where(WorkflowTemplateModel.is_active.is_(True))
        stmt = stmt.order_by(WorkflowTemplateModel.sort_order)
        models = self.session.execute(stmt).scalars().all()
        return [self._model_to_entity(m) for m in models]

    def find_by_name(self, company_id: str, name: str) -> Optional[WorkflowTemplate]:
        m = self.session.execute(
            select(WorkflowTemplateModel).where(
                WorkflowTemplateModel.company_id == company_id,
                WorkflowTemplateModel.name == name,
            )
        ).scalar_one_or_none()
        return self._model_to_entity(m) if m else None

    def delete(self, id: str) -> None:
        model = self.session.execute(
            select(WorkflowTemplateModel).where(
                WorkflowTemplateModel.id == id
            )
        ).scalar_one_or_none()
        if model:
            self.session.delete(model)
            self.session.flush()

    def has_requests(self, template_id: str) -> bool:
        from src.request_bc.request.infrastructure.models import ServiceRequestModel

        result = self.session.execute(
            select(ServiceRequestModel.id).where(
                ServiceRequestModel.workflow_template_id == template_id
            ).limit(1)
        ).scalar_one_or_none()
        return result is not None
